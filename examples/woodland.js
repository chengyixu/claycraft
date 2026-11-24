import * as THREE from 'three';

export function dressWoodland(scene) {
  let seed = 814;
  function random() {
    seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
    return seed / 4294967296;
  }
  function painted(width, height, draw) {
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    draw(canvas.getContext('2d'));
    const texture = new THREE.CanvasTexture(canvas);
    texture.colorSpace = THREE.SRGBColorSpace;
    return texture;
  }
  scene.background = painted(1024, 768, ctx => {
    const sky = ctx.createLinearGradient(0, 0, 1024, 768);
    sky.addColorStop(0, '#d7b988'); sky.addColorStop(.43, '#a6a284'); sky.addColorStop(1, '#5d6650');
    ctx.fillStyle = sky; ctx.fillRect(0, 0, 1024, 768);
    for (let index = 0; index < 85; index++) {
      const horizontal = random() * 1150 - 60;
      const thickness = 3 + random() ** 3 * 65;
      ctx.filter = `blur(${7 + random() * 14}px)`;
      ctx.strokeStyle = `rgba(54,55,37,${.06 + random() * .16})`;
      ctx.lineWidth = thickness;
      ctx.beginPath(); ctx.moveTo(horizontal, 790);
      ctx.lineTo(horizontal + random() * 130 - 65, -30); ctx.stroke();
    }
    const colors = ['#ffe3ac', '#e3c887', '#69774a', '#526342', '#e3d6a4'];
    for (let index = 0; index < 330; index++) {
      ctx.filter = `blur(${5 + random() * 18}px)`;
      ctx.globalAlpha = .13 + random() * .24;
      ctx.fillStyle = colors[index % colors.length];
      ctx.beginPath(); ctx.arc(random() * 1024, random() * 700 - 80, 3 + random() ** 2 * 47, 0, Math.PI * 2); ctx.fill();
    }
  });
  const wood = painted(1024, 512, ctx => {
    const image = ctx.createImageData(1024, 512);
    for (let row = 0; row < 512; row++) {
      for (let column = 0; column < 1024; column++) {
        const warp = row + 7 * Math.sin(column * .005 + row * .016) + 2 * Math.sin(column * .019 - row * .023);
        const grain = 5 * Math.sin(warp * .22) + 2.8 * Math.sin(warp * 1.9) + 2.8 * (random() - .5);
        const pixel = (row * 1024 + column) * 4;
        image.data.set([143 + grain, 103 + grain, 72 + grain, 255], pixel);
      }
    }
    ctx.putImageData(image, 0, 0);
  });
  wood.wrapS = wood.wrapT = THREE.RepeatWrapping;
  wood.repeat.set(3, 4);
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(22, 9), new THREE.MeshStandardMaterial({map: wood, roughness:.87}));
  floor.rotation.x = -Math.PI / 2;
  floor.position.set(0, -.229, 2.40);
  scene.add(floor);
  floor.receiveShadow = true;

  const grit = painted(256, 256, ctx => {
    ctx.fillStyle = '#ded9c7'; ctx.fillRect(0, 0, 256, 256);
    for (let index = 0; index < 10500; index++) {
      ctx.fillStyle = random() < .5 ? '#9e937c' : '#fff3da';
      ctx.globalAlpha = .15 + random() * .45;
      ctx.fillRect(random() * 256, random() * 256, 1 + random() * 2, 1 + random());
    }
  });
  grit.wrapS = grit.wrapT = THREE.RepeatWrapping;
  const matte = color => new THREE.MeshStandardMaterial({color, map: grit, bumpMap: grit, bumpScale:.007, roughness:.98});
  const soil = new THREE.CylinderGeometry(1, 1, 1, 140, 12);
  const pos = soil.attributes.position;
  const colors = [];
  const tone = new THREE.Color();
  for (let index = 0; index < pos.count; index++) {
    const horizontal = pos.getX(index), depth = pos.getZ(index), level = pos.getY(index);
    const angle = Math.atan2(depth, horizontal);
    const rim = 1 + .032 * Math.sin(5*angle) + .019 * Math.cos(9*angle) + .009 * Math.sin(23*angle);
    const edge = 1 - .033 * (2 * level) ** 4;
    pos.setXYZ(index, horizontal * 2.45 * rim * edge, -.118 + level*.215 + .007*Math.sin(7*angle), depth * 1.16 * rim * edge);
    tone.set(level > .49 ? 0x8f8961 : level > .31 ? 0x807751 : level > -.25 ? 0xb2976e : 0x877051);
    tone.multiplyScalar(.89 + random()*.18);
    colors.push(tone.r,tone.g,tone.b);
  }
  soil.computeVertexNormals();
  soil.setAttribute('color', new THREE.Float32BufferAttribute(colors,3));
  const bed = new THREE.Mesh(soil, new THREE.MeshStandardMaterial({vertexColors:true,map:grit,bumpMap:grit,bumpScale:.012,roughness:1}));
  scene.add(bed);
  const leaf = new THREE.BufferGeometry();
  const leafPositions = [], leafIndices = [];
  for (let row = 0; row <= 10; row++) {
    const fraction = row / 10, width = Math.sin(Math.PI*fraction)**.83 * .50;
    leafPositions.push(-width, fraction, .16*fraction**2, 0, fraction, .09*width+.16*fraction**2, width, fraction,.16*fraction**2);
    if (row) {
      const base = row*3;
      leafIndices.push(base-3,base,base-2,base-2,base,base+1,base-2,base+1,base-1,base-1,base+1,base+2);
    }
  }
  leaf.setAttribute('position',new THREE.Float32BufferAttribute(leafPositions,3)); leaf.setIndex(leafIndices); leaf.computeVertexNormals();
  const foliage = [0x808a50,0x586c43,0x9c9854,0xb3aa64,0x6c8050];
  const blades = [];
  function blade(point, direction, width, color) {
    const pose = new THREE.Object3D();
    pose.position.copy(point);
    pose.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),direction.clone().normalize());
    pose.scale.set(width,direction.length(),width);
    pose.updateMatrix();
    blades.push([pose.matrix,color]);
  }
  for (const [horizontal,depth,scale] of [[-1.53,-.35,.69],[1.66,-.29,.80],[1.39,.10,.34],[-1.68,.34,.30],[-.96,-.68,.47],[.81,-.78,.42]]) {
    for (let frond=0; frond<7; frond++) {
      const angle=frond*2.4+random()*.4, length=scale*(.64+random()*.4);
      const horizontalAxis=new THREE.Vector3(Math.cos(angle),0,Math.sin(angle));
      const across=new THREE.Vector3(-horizontalAxis.z,0,horizontalAxis.x);
      const base=new THREE.Vector3(horizontal,-.002,depth);
      function stem(fraction) {
        return base.clone().addScaledVector(horizontalAxis,length*fraction*.66).addScaledVector(new THREE.Vector3(0,1,0),length*(1.38*fraction-.72*fraction**2));
      }
      for (let pair=0; pair<10; pair++) {
        const fraction=(pair+1)/11, at=stem(fraction);
        blade(stem(pair/11),at.clone().sub(stem(pair/11)),.009,0x818453);
        for (const side of [-1,1]) {
          const reach=length*(.045+.20*Math.sin(Math.PI*fraction));
          const tip=across.clone().multiplyScalar(side*reach).addScaledVector(horizontalAxis,reach*.46);
          tip.y=reach*.47;
          blade(at,tip,reach*.30,foliage[(frond+pair%3)%foliage.length]);
        }
      }
    }
  }
  const leaves = new THREE.InstancedMesh(leaf,new THREE.MeshStandardMaterial({side:THREE.DoubleSide,roughness:1}),blades.length);
  blades.forEach(([matrix,color],index)=>{ leaves.setMatrixAt(index,matrix); leaves.setColorAt(index,new THREE.Color(color)); });
  scene.add(leaves);
  const pebbles = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1,1),matte(0xffffff),210);
  const pose = new THREE.Object3D();
  for (let index=0; index<pebbles.count; index++) {
    const angle=random()*Math.PI*2, radius=.48+.49*Math.sqrt(random()), size=.009+random()**3*.052;
    pose.position.set(2.42*radius*Math.cos(angle),-.008+size*.25,1.12*radius*Math.sin(angle));
    pose.rotation.set(random(),random()*6,random()); pose.scale.set(size*1.6,size*.6,size);
    pose.updateMatrix(); pebbles.setMatrixAt(index,pose.matrix);
    pebbles.setColorAt(index,new THREE.Color([0x90856c,0xaaa085,0x70664f,0x90864c][index%4]));
  }
  scene.add(pebbles);
  const contact = painted(128,128,ctx=>{
    const shadow=ctx.createRadialGradient(64,64,0,64,64,64);
    shadow.addColorStop(0,'rgba(39,28,15,.65)'); shadow.addColorStop(.4,'rgba(52,39,20,.38)'); shadow.addColorStop(1,'rgba(60,45,24,0)');
    ctx.fillStyle=shadow;ctx.fillRect(0,0,128,128);
  });
  const shadow = new THREE.Mesh(new THREE.PlaneGeometry(.72,.50),new THREE.MeshBasicMaterial({map:contact,transparent:true,depthWrite:false,polygonOffset:true,polygonOffsetFactor:-2}));
  shadow.rotation.x = -Math.PI/2;shadow.position.y=.003;scene.add(shadow);
  return shadow;
}
