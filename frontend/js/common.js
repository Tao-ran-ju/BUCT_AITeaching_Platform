const as=document.querySelectorAll(".shortcut .wrapper ul a");
const underline=document.querySelector(".shortcut .wrapper .underline");
const wrapper=document.querySelector(".shortcut .wrapper");

underline.style.left=`${a.getBoundingClientRect().left-wrapper.getBoundingClientRect().left+15}px`

for(let i=0;i<as.length;i++){
    as[i].addEventListener('mouseenter',function(e){
        this.classList.add('activated');
        const a_rect=as[i].getBoundingClientRect();
        const wrapper_rect=wrapper.getBoundingClientRect();
        underline.style.left=`${a_rect.left-wrapper_rect.left+15}px`;
    })
    as[i].addEventListener('mouseleave',function(e){
        this.classList.remove('activated');
    })
}