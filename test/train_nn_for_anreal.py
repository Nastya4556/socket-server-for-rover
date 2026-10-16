# -*- coding: utf-8 -*-
"""
Обучение нейронной сети для Анрила.
Данные берутся из папки telemetry_for_anreal/ рядом со скриптом.
"""

import torch
import torch.nn as nn
import pandas as pd
import numpy as np
import glob
import os
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime

# ── Конфигурация ────────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parent
DATA_DIR    = BASE_DIR / "telemetry_for_anreal"
CSV_GLOB    = str(DATA_DIR / "*.csv")          # любые csv, в т.ч. combined.csv
MODEL_DIR   = BASE_DIR / "best_model_for_anreal"
_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
MODEL_PATH = str(MODEL_DIR / f"momentum_rnn_anreal_{_ts}.pt")

# ── Чтение параметров обучения из GUI ───────────────────────────
_params_path = BASE_DIR / "params_for_train_nn_for_anreal.json"
if _params_path.exists():
    try:
        _p = __import__("json").loads(_params_path.read_text(encoding="utf-8"))
        EPOCHS = int(_p.get("epochs", 600))
        LR     = float(_p.get("lr", 1e-3))
    except Exception:
        EPOCHS = 600
        LR     = 1e-3
else:
    EPOCHS = 600
    LR     = 1e-3

TEST_SIZE   = 0.15

SEQ_LEN     = 150
CHUNK_LEN   = 150
HIDDEN_SIZE = 64
NUM_LAYERS  = 2

INPUT_COLS  = [
    "angular_velocity_fl_mps",
    "angular_velocity_fr_mps",
    "angular_velocity_rl_mps",
    "angular_velocity_rr_mps",
    "yaw_difference",
    "initial_momentum",
]
OUTPUT_COLS = ["momentum_fl", "momentum_fr", "momentum_rl", "momentum_rr"]

# ── 1. Загрузка данных ──────────────────────────────────────────
files = sorted(glob.glob(CSV_GLOB))
if not files:
    raise FileNotFoundError(f"Не найдено файлов по маске {CSV_GLOB}\n"
                            f"Убедитесь что папка {DATA_DIR} содержит файлы telemetry_*.csv")

print(f"Найдено файлов телеметрии: {len(files)}")

dfs = []
for f in files:
    df = pd.read_csv(f)
    missing = [c for c in INPUT_COLS + OUTPUT_COLS if c not in df.columns]
    if missing:
        print(f"  пропускаю {f}: нет колонок {missing}")
        continue
    dfs.append((f, df))

print(f"Используется файлов: {len(dfs)}")
if not dfs:
    raise ValueError("Нет подходящих файлов с нужными колонками")

# ── 2. Разбивка train/test по файлам ────────────────────────────
rng = np.random.RandomState(42)
if len(dfs) == 1:
    # единственный файл — весь идёт в train, валидация тоже на нём
    train_files = dfs
    test_files  = dfs
    print("Один файл: используется для train и val одновременно")
else:
    idx = rng.permutation(len(dfs))
    n_test = max(1, int(len(dfs) * TEST_SIZE))
    test_idx = set(idx[:n_test])
    train_files = [dfs[i] for i in range(len(dfs)) if i not in test_idx]
    test_files  = [dfs[i] for i in range(len(dfs)) if i in test_idx]
print(f"Train файлов: {len(train_files)}, Test файлов: {len(test_files)}")

# ── 3. Нормализация ──────────────────────────────────────────────
X_train_concat = np.concatenate(
    [df[INPUT_COLS].values.astype(np.float32) for _, df in train_files], axis=0)
y_train_concat = np.concatenate(
    [df[OUTPUT_COLS].values.astype(np.float32) for _, df in train_files], axis=0)

scaler_X = MinMaxScaler()
scaler_y = MinMaxScaler()
scaler_X.fit(X_train_concat)
scaler_y.fit(y_train_concat)


def normalize(df):
    X = scaler_X.transform(df[INPUT_COLS].values.astype(np.float32)).astype(np.float32)
    y = scaler_y.transform(df[OUTPUT_COLS].values.astype(np.float32)).astype(np.float32)
    return X, y


# ── 4. Тестовые окна для валидации ──────────────────────────────
def make_eval_sequences(X, y, seq_len):
    Xs, ys = [], []
    for i in range(len(X) - seq_len):
        Xs.append(X[i: i + seq_len])
        ys.append(y[i + seq_len])
    return np.array(Xs), np.array(ys)


X_test_list, y_test_list = [], []
for _, df in test_files:
    X, y = normalize(df)
    Xs, ys = make_eval_sequences(X, y, SEQ_LEN)
    if len(Xs) > 0:
        X_test_list.append(Xs)
        y_test_list.append(ys)

X_test = torch.from_numpy(np.concatenate(X_test_list, axis=0))
y_test = torch.from_numpy(np.concatenate(y_test_list, axis=0))
print(f"Test окон (eval): {len(X_test)}")

# ── 5. Архитектура ───────────────────────────────────────────────
class MomentumRNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.rnn = nn.RNN(
            input_size=len(INPUT_COLS),
            hidden_size=HIDDEN_SIZE,
            num_layers=NUM_LAYERS,
            batch_first=True,
            dropout=0.1,
            nonlinearity="tanh",
        )
        self.head = nn.Sequential(
            nn.Linear(HIDDEN_SIZE, 32),
            nn.ReLU(),
            nn.Linear(32, len(OUTPUT_COLS)),
            nn.Sigmoid(),
        )

    def forward(self, x, state=None):
        out, state = self.rnn(x, state)
        pred_seq = self.head(out)
        return pred_seq, state


model = MomentumRNN()
print(f"Параметров: {sum(p.numel() for p in model.parameters()):,}")

optimizer     = torch.optim.Adam(model.parameters(), lr=LR)
scheduler     = torch.optim.lr_scheduler.StepLR(optimizer, step_size=100, gamma=0.5)
loss_fn       = nn.MSELoss()
best_val_loss = float("inf")

# ── 6. Train-последовательности для TBPTT ───────────────────────
train_sequences = []
for _, df in train_files:
    X, y = normalize(df)
    train_sequences.append((torch.from_numpy(X), torch.from_numpy(y)))


def iterate_chunks(X, y, chunk_len):
    n = len(X)
    for start in range(0, n - 1, chunk_len):
        end = min(start + chunk_len, n)
        if end - start < 2:
            continue
        yield X[start:end].unsqueeze(0), y[start:end].unsqueeze(0)


# ── 7. Обучение ──────────────────────────────────────────────────
for epoch in range(1, EPOCHS + 1):
    model.train()
    order = rng.permutation(len(train_sequences))
    epoch_loss, n_batches = 0.0, 0

    for file_idx in order:
        X_seq, y_seq = train_sequences[file_idx]
        state = None

        for xb, yb in iterate_chunks(X_seq, y_seq, CHUNK_LEN):
            optimizer.zero_grad()
            pred_seq, state = model(xb, state)
            loss = loss_fn(pred_seq, yb)
            loss.backward()
            optimizer.step()
            state = state.detach()
            epoch_loss += loss.item()
            n_batches += 1

    scheduler.step()

    if epoch % 30 == 0 or epoch == 1:
        model.eval()
        with torch.no_grad():
            pred_test, _ = model(X_test)
            pred_last = pred_test[:, -1, :]
            val_loss = loss_fn(pred_last, y_test).item()
            pred_real = scaler_y.inverse_transform(pred_last.numpy())
            true_real = scaler_y.inverse_transform(y_test.numpy())
            mae = np.mean(np.abs(pred_real - true_real))

        train_loss = epoch_loss / max(n_batches, 1)
        print(f"Epoch {epoch:3d} | train MSE: {train_loss:.5f} | val MSE: {val_loss:.5f} | MAE реальный: {mae:.2f}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save({
                "model_state": model.state_dict(),
                "scaler_X":    scaler_X,
                "scaler_y":    scaler_y,
                "input_cols":  INPUT_COLS,
                "output_cols": OUTPUT_COLS,
                "hidden_size": HIDDEN_SIZE,
                "num_layers":  NUM_LAYERS,
                "seq_len":     SEQ_LEN,
            }, MODEL_PATH)

print(f"\nЛучшая модель сохранена → {MODEL_PATH}")