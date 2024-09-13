const getPlainText = (text) => {
    return text.normalize('NFD').replace(/[\u0300-\u036f]/g, '')
}

const doSearch = (e) => {
    const pattern = new RegExp(getPlainText(e.target.value), 'i')
    for(const article of document.querySelectorAll('article')) {
        const found = getPlainText(article.textContent).search(pattern) !== -1
        article.style.display = found ? 'inherit' : 'none'
    }
}

const loadSearch = () => {
    const search = document.querySelector('#search')
    if(search) {
        const input = document.createElement('input')
        input.onkeyup = doSearch
        search.appendChild(input)
    }
}

addEventListener('load', loadSearch)
