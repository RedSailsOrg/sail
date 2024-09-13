const createFloater = () => {
    const footArea = document.querySelector('.footnote')
    if(!footArea) { return }

    const floater = document.createElement('ol')
    floater.classList.add('floater')
    document.body.appendChild(floater)

    const inlines = [...document.querySelectorAll('.footnote-ref')]
    const footnotes = [...document.querySelectorAll('.footnote-backref')]

    /*
    triplet:
    1. reference element: presence in viewframe leads to real display
    2. real: the real object that we want to display
    3. clone: the clone comes and goes
    */
    const triplets = [];
    inlines.map((inline, idx) => {
        if( !footArea.contains(inline) ){
            real = footnotes[idx].parentNode;
            clone = document.createElement('p');
            clone.innerHTML = real.innerHTML;
            floater.appendChild(clone);
            triplets.push({inline, real, clone});
        }
    });

    const act = updateFloater(floater, triplets);
    act();
    addEventListener('scroll', act);
}
const updateFloater = (floater, allInlines) => () => {
    const selected = new Set()
    for(const {inline, real, clone} of allInlines) {
        const {top: tr, bottom: br} = real.getBoundingClientRect()
        const footOnScreen = (tr > 0 && br / innerHeight < 1)

        const {top: ti, bottom: bi} = inline.getBoundingClientRect()
        const inlineOnScreen = (ti / innerHeight > .1 && bi / innerHeight < .7)

        clone.style.display = 'none';
        if(!footOnScreen && inlineOnScreen) selected.add(clone)
    }

    for(const clone of selected) {
        clone.style.display = 'block';
        if(floater.getBoundingClientRect().height / innerHeight > .2) break
    }
}
addEventListener('load', createFloater)
