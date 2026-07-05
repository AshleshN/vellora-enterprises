document.querySelectorAll(".tilt").forEach(card => {
    card.addEventListener("mousemove", e => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const centerX = rect.width / 2;
        const centerY = rect.height / 2;

        const rotateX = -(y - centerY) / 15;
        const rotateY = (x - centerX) / 15;

        card.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
    });

    card.addEventListener("mouseleave", () => {
        card.style.transform = "rotateX(0) rotateY(0)";
    });
});

const pills = document.querySelectorAll(".category-pill");

pills.forEach(pill => {

    pill.addEventListener("click", () => {

        pills.forEach(p =>
            p.classList.remove("active")
        );

        pill.classList.add("active");

    });

});

const toast = document.querySelector(".toast");

if (toast){

    setTimeout(()=>{

        toast.style.transition="0.4s";
        toast.style.opacity="0";
        toast.style.transform="translateX(120px)";

        setTimeout(()=>{

            toast.remove();

        },400);

    },3000);

}
