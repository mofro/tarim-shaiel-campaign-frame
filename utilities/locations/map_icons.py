"""
Canvas-drawn MapLibre marker icon registration JS.

Shared by generate_locations_html.py (world home map) and
location_components.py (mini-maps on location/region detail pages).

REGISTERED_ICONS lists every icon name registered by icon_registration_js().
It is used by categories.check_icon_coverage() to cross-validate the category→icon
mapping in categories.ICON_MAP against what is actually available at runtime.
Keep this set in sync with the _mk() calls below.
"""

REGISTERED_ICONS: frozenset[str] = frozenset({
    "cat-city",
    "cat-town",
    "cat-route-node",
    "cat-sacred-site",
    "cat-fortress",
    "cat-oasis",
    "cat-landmark",
    "cat-poi",
    "cat-dungeon",
})


def icon_registration_js() -> str:
    """Return the JS IIFE that registers all canvas-drawn marker images.

    Must be called inside map.on('load', ...) before any symbol layer is added.
    """
    return (
        '(function(){'
        'function _mk(name,draw){var c=document.createElement("canvas");c.width=32;c.height=32;var ctx=c.getContext("2d");draw(ctx);var d=ctx.getImageData(0,0,32,32);map.addImage(name,{width:32,height:32,data:d.data});}'
        '_mk("cat-city",function(ctx){'
          'ctx.strokeStyle="#7a1f1f";ctx.lineWidth=2.5;ctx.fillStyle="#7a1f1f";'
          'ctx.beginPath();ctx.arc(16,16,13,0,Math.PI*2);ctx.stroke();'
          'ctx.beginPath();ctx.arc(16,16,6,0,Math.PI*2);ctx.fill();'
        '});'
        '_mk("cat-town",function(ctx){'
          'ctx.strokeStyle="#7a1f1f";ctx.lineWidth=2.5;ctx.fillStyle="#7a1f1f";'
          'ctx.beginPath();ctx.rect(4,4,24,24);ctx.stroke();'
          'ctx.beginPath();ctx.arc(16,16,5,0,Math.PI*2);ctx.fill();'
        '});'
        '_mk("cat-route-node",function(ctx){'
          'ctx.strokeStyle="#7a1f1f";ctx.lineWidth=2.5;ctx.fillStyle="#7a1f1f";'
          'ctx.beginPath();ctx.moveTo(16,2);ctx.lineTo(30,16);ctx.lineTo(16,30);ctx.lineTo(2,16);ctx.closePath();ctx.stroke();'
          'ctx.beginPath();ctx.arc(16,16,4,0,Math.PI*2);ctx.fill();'
        '});'
        '_mk("cat-sacred-site",function(ctx){'
          'ctx.beginPath();ctx.moveTo(7,29);ctx.lineTo(7,17);'
          'ctx.quadraticCurveTo(7,3,16,3);ctx.quadraticCurveTo(25,3,25,17);'
          'ctx.lineTo(25,29);ctx.closePath();'
          'ctx.fillStyle="#b8892a";ctx.fill();'
          'ctx.strokeStyle="#7a1f1f";ctx.lineWidth=1.5;ctx.stroke();'
        '});'
        '_mk("cat-fortress",function(ctx){'
          'ctx.beginPath();'
          'ctx.moveTo(4,8);ctx.lineTo(10,8);ctx.lineTo(10,16);ctx.lineTo(13,16);'
          'ctx.lineTo(13,8);ctx.lineTo(19,8);ctx.lineTo(19,16);ctx.lineTo(22,16);'
          'ctx.lineTo(22,8);ctx.lineTo(28,8);ctx.lineTo(28,28);ctx.lineTo(4,28);ctx.closePath();'
          'ctx.fillStyle="#7a1f1f";ctx.fill();'
          'ctx.strokeStyle="#b8892a";ctx.lineWidth=1.5;ctx.stroke();'
        '});'
        '_mk("cat-oasis",function(ctx){'
          'var pts=[[16,16,16,3],[16,16,26.9,9.5],[16,16,22.5,23.5],[16,16,9.5,23.5],[16,16,5.1,9.5]];'
          'ctx.lineCap="round";'
          'ctx.strokeStyle="#7a1f1f";ctx.lineWidth=6;'
          'pts.forEach(function(p){ctx.beginPath();ctx.moveTo(p[0],p[1]);ctx.lineTo(p[2],p[3]);ctx.stroke();});'
          'ctx.strokeStyle="#b8892a";ctx.lineWidth=4;'
          'pts.forEach(function(p){ctx.beginPath();ctx.moveTo(p[0],p[1]);ctx.lineTo(p[2],p[3]);ctx.stroke();});'
          'ctx.fillStyle="#b8892a";ctx.beginPath();ctx.arc(16,16,5,0,Math.PI*2);ctx.fill();'
          'ctx.strokeStyle="#7a1f1f";ctx.lineWidth=1.5;ctx.beginPath();ctx.arc(16,16,5,0,Math.PI*2);ctx.stroke();'
        '});'
        '_mk("cat-landmark",function(ctx){'
          'ctx.beginPath();ctx.moveTo(2,28);'
          'ctx.quadraticCurveTo(5,14,11,12);ctx.quadraticCurveTo(14,6,17,12);'
          'ctx.quadraticCurveTo(22,14,30,28);ctx.closePath();'
          'ctx.fillStyle="#7a1f1f";ctx.fill();'
          'ctx.strokeStyle="#b8892a";ctx.lineWidth=1.5;ctx.stroke();'
        '});'
        '_mk("cat-poi",function(ctx){'
          'ctx.fillStyle="#7a1f1f";'
          'ctx.beginPath();ctx.arc(16,16,9,0,Math.PI*2);ctx.fill();'
        '});'
        '_mk("cat-dungeon",function(ctx){'
          'ctx.strokeStyle="#5a4020";ctx.lineWidth=2;ctx.lineCap="round";ctx.fillStyle="#5a4020";'
          'var sa=Math.atan2(4.2-16,21.5-16),ea=Math.atan2(4.2-16,10.5-16);'
          'ctx.beginPath();ctx.arc(16,16,13,sa,ea,true);ctx.stroke();'
          'ctx.beginPath();ctx.arc(16,16,8,0,Math.PI*2);ctx.stroke();'
          'ctx.beginPath();ctx.arc(16,16,3.5,0,Math.PI*2);ctx.fill();'
        '});'
        '})();\n'
    )
