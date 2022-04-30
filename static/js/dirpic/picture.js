var pic = document.getElementById('picture')

pic.addEventListener('click', function (event) {
    pic_zoom(event.clientX, event.clientY, pic.width, pic.height)
})

//pic.addEventListener('auxclick', function (event) {
//    history.back()
//})

function pic_zoom(x, y, w, h) {
    if (pic.style.maxHeight == '100vh' || !pic.style.maxHeight) {
        pic.style.maxHeight = 'none'
        pic.style.maxWidth = 'none'
        var bigX = x * (pic.width / w)
        var bigY = y * (pic.height / h)
        var canvasW2 = window.innerWidth/2
        var canvasH2 = window.innerHeight/2
        var scrollX = bigX > canvasW2 ? bigX - canvasW2 : 0
        var scrollY = bigY > canvasH2 ? bigY - canvasH2 : 0
        window.scrollTo({
            top:scrollY,
            left:scrollX,
            behavior:'instant'
        })
    } else {
        pic.style.maxHeight = '100vh'
        pic.style.maxWidth = '100%'
        window.scrollTo({top:0, left:0, behavior:'instant'})
    }
}
