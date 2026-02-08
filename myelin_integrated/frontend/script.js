const c = document.getElementById("particles");
const ctx = c.getContext("2d");

c.width = innerWidth;
c.height = innerHeight;

let dots = [];
for(let i=0;i<35;i++){
  dots.push({
    x:Math.random()*c.width,
    y:Math.random()*c.height,
    r:1 + Math.random()*2,
    dx:(Math.random()-.5)*0.6,
    dy:(Math.random()-.5)*0.6
  })
}

function animate(){
  ctx.clearRect(0,0,c.width,c.height);
  ctx.fillStyle="rgba(255,255,255,.8)";

  dots.forEach(d=>{
    ctx.beginPath();
    ctx.arc(d.x,d.y,d.r,0,Math.PI*2);
    ctx.fill();

    d.x+=d.dx;
    d.y+=d.dy;

    if(d.x<0||d.x>c.width) d.dx*=-1;
    if(d.y<0||d.y>c.height) d.dy*=-1;
  });

  requestAnimationFrame(animate);
}
animate();

addEventListener("resize",()=>{
  c.width=innerWidth;
  c.height=innerHeight;
});
