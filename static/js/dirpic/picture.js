var pic = document.getElementById('picture')

pic.addEventListener('click', function (event) {
    history.back()
})
pic.addEventListener('auxclick', function (event) {
    pic_zoom()
})

function pic_zoom() {
    if (pic.style.maxHeight == '100vh' || !pic.style.maxHeight) {
        pic.style.maxHeight = 'none'
        pic.style.maxWidth = 'none'
    } else {
        pic.style.maxHeight = '100vh'
        pic.style.maxWidth = '100%'
        window.scrollTo({top:0, left:0, behavior:'instant'})
    }
}