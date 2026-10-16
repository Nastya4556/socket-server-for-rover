const canvas = document.getElementById("canvas")
const svg = document.getElementById("connections")

let modules = {}
let edges = []

let dragModule = null
let dragOffsetX = 0
let dragOffsetY = 0

async function loadGraph() {

    const res = await fetch("/api/graph")
    const data = await res.json()

    modules = {}
    edges = data.edges || []

    data.nodes.forEach((n, i) => {

        modules[n.id] = {
            ...n,
            x: 100 + i * 260,
            y: 120
        }

    })

    renderModules()
    renderEdges()
}

function reloadGraph(){
    loadGraph()
}

function renderModules() {

    canvas.innerHTML = ""

    Object.values(modules).forEach(m => {

        const div = document.createElement("div")
        div.className = "module"
        if (m.running) div.classList.add("running")

        div.style.left = m.x + "px"
        div.style.top = m.y + "px"

        div.dataset.name = m.id

        const title = document.createElement("div")
        title.className = "module-title"
        title.innerText = m.id + " (" + m.type + ")"

        title.onmousedown = startDrag

        const body = document.createElement("div")
        body.className = "module-body"

        const inputs = document.createElement("div")
        inputs.className = "ports inputs"

        if (m.accepts_any_input) {

            const p = document.createElement("div")
            p.className = "port input"
            p.innerText = "*"

            p.dataset.module = m.id
            p.dataset.port = "*"
            p.dataset.type = "input"

            inputs.appendChild(p)

        } else {

            m.inputs.forEach(sig => {

                const p = document.createElement("div")
                p.className = "port input"
                p.innerText = sig

                p.dataset.module = m.id
                p.dataset.port = sig
                p.dataset.type = "input"

                inputs.appendChild(p)

            })

        }

        const outputs = document.createElement("div")
        outputs.className = "ports outputs"

        m.outputs.forEach(sig => {

            const p = document.createElement("div")
            p.className = "port output"
            p.innerText = sig

            p.dataset.module = m.id
            p.dataset.port = sig
            p.dataset.type = "output"

            p.onclick = startConnection

            outputs.appendChild(p)

        })

        body.appendChild(inputs)
        body.appendChild(outputs)

        const controls = document.createElement("div")

        const startBtn = document.createElement("button")
        startBtn.innerText = "start"
        startBtn.onclick = () => startModule(m.id)

        const delBtn = document.createElement("button")
        delBtn.innerText = "delete"
        delBtn.onclick = () => deleteModule(m.id)

        controls.appendChild(startBtn)
        controls.appendChild(delBtn)

        div.appendChild(title)
        div.appendChild(body)
        div.appendChild(controls)

        canvas.appendChild(div)

    })

}

function renderEdges() {

    svg.innerHTML = ""

    edges.forEach(e => {

        const outPort = document.querySelector(
            `.port.output[data-module="${e.from}"][data-port="${e.signal}"]`
        )

        let inPort = document.querySelector(
            `.port.input[data-module="${e.to}"][data-port="${e.signal}"]`
        )

        if (!inPort) {
            inPort = document.querySelector(
                `.port.input[data-module="${e.to}"][data-port="*"]`
            );
        }

        if (!outPort || !inPort) return

        const r1 = outPort.getBoundingClientRect()
        const r2 = inPort.getBoundingClientRect()

        const canvasRect = canvas.getBoundingClientRect()

        const x1 = r1.right - canvasRect.left
        const y1 = r1.top + r1.height/2 - canvasRect.top

        const x2 = r2.left - canvasRect.left
        const y2 = r2.top + r2.height/2 - canvasRect.top

        const dx = Math.abs(x2 - x1) * 0.5

        const path = document.createElementNS(
            "http://www.w3.org/2000/svg",
            "path"
        )

        const d =
            `M ${x1} ${y1}
             C ${x1+dx} ${y1},
               ${x2-dx} ${y2},
               ${x2} ${y2}`

        path.setAttribute("d", d)
        path.setAttribute("stroke", "#444")
        path.setAttribute("fill", "none")
        path.setAttribute("stroke-width", "2")

        svg.appendChild(path)

    })

}

function startDrag(e){

    const module = e.target.closest(".module")

    dragModule = modules[module.dataset.name]

    dragOffsetX = e.offsetX
    dragOffsetY = e.offsetY

    document.addEventListener("mousemove", dragMove)
    document.addEventListener("mouseup", stopDrag)

}

function dragMove(e){

    if(!dragModule) return

    const rect = canvas.getBoundingClientRect()

    dragModule.x = e.clientX - rect.left - dragOffsetX
    dragModule.y = e.clientY - rect.top - dragOffsetY

    renderModules()
    renderEdges()

}

function stopDrag(){

    dragModule = null

    document.removeEventListener("mousemove", dragMove)
    document.removeEventListener("mouseup", stopDrag)

}

let connectionStart = null

function startConnection(e){

    connectionStart = {
        module: e.target.dataset.module,
        port: e.target.dataset.port
    }

    document.querySelectorAll(".port.input").forEach(p => {

        p.onclick = finishConnection

    })

}

async function finishConnection(e){

    if(!connectionStart) return

    const receiver = e.target.dataset.module

    const bd = JSON.stringify({
            sender: connectionStart.module,
            receiver: receiver,
            signature: connectionStart.port
        })

    console.log("11111111111")
    console.log(e)
    console.log(e.target)
    console.log("22222222222")

    await fetch("/api/connect",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: bd
    })

    connectionStart = null

    loadGraph()

}

async function startModule(name){

    await fetch("/api/start/"+name,{method:"POST"})

    loadGraph()

}

async function deleteModule(name){

    await fetch("/api/modules/"+name,{method:"DELETE"})

    loadGraph()

}

async function loadModuleTypes(){

    const res = await fetch("/api/modules/available")
    const data = await res.json()

    const select = document.getElementById("moduleType")

    select.innerHTML=""

    Object.keys(data).forEach(name => {

        const opt = document.createElement("option")
        opt.value = name
        opt.innerText = name

        select.appendChild(opt)

    })

}

async function createModule(){

    const type = document.getElementById("moduleType").value
    const name = document.getElementById("moduleName").value

    if(!name){
        alert("module name required")
        return
    }

    await fetch("/api/modules/create",{

        method:"POST",
        headers:{
            "Content-Type":"application/json"
        },

        body:JSON.stringify({
            type:type,
            name:name,
            config:{}
        })

    })

    document.getElementById("moduleName").value=""

    loadGraph()

}

window.reloadGraph = reloadGraph
window.createModule = createModule

loadModuleTypes()
loadGraph()