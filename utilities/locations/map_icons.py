"""
Canvas-drawn MapLibre marker icon registration JS.

Shared by generate_locations_html.py (world home map) and
location_components.py (mini-maps on location/region detail pages).

REGISTERED_ICONS lists every icon name registered by icon_registration_js().
It is used by categories.check_icon_coverage() to cross-validate the category→icon
mapping in categories.ICON_MAP against what is actually available at runtime.
Keep this set in sync with the _mk() calls below.

Icons are drawn at 64×64 px and registered via ImageData + { pixelRatio: 2 } so
MapLibre treats them as 32 logical px at @2x density — sharp on retina and standard
displays. Note: MapLibre's addImage() accepts ImageData / {width,height,data}, not a
raw HTMLCanvasElement; getImageData() is used to extract pixel bytes before adding.
All stroke widths are 2.5 px on the 64×64 canvas, which appears as ~1.25 px visually.
"""

REGISTERED_ICONS: frozenset[str] = frozenset({
    "cat-city",
    "cat-capital",
    "cat-town",
    "cat-route-node",
    "cat-sacred-site",
    "cat-fortress",
    "cat-oasis",
    "cat-landmark",
    "cat-lake",
    "cat-poi",
    "cat-dungeon",
})


def icon_registration_js() -> str:
    """Return the JS IIFE that registers all canvas-drawn marker images.

    Must be called inside map.on('load', ...) before any symbol layer is added.
    """
    return (
        '(function(){'
        # _mk draws at 64×64 and registers at pixelRatio:2 (32 logical px, @2x sharp)
        'function _mk(name,draw){var c=document.createElement("canvas");c.width=64;c.height=64;var ctx=c.getContext("2d");draw(ctx);var d=ctx.getImageData(0,0,64,64);map.addImage(name,{width:64,height:64,data:d.data},{pixelRatio:2});}'

        # capital — gold 5-pointed star backing + city ring + inner dot
        '_mk("cat-capital",function(ctx){'
          'ctx.fillStyle="#b8892a";ctx.beginPath();'
          'for(var i=0;i<10;i++){var r=(i%2===0)?32:12;var a=i*Math.PI/5-Math.PI/2;'
          'i===0?ctx.moveTo(32+r*Math.cos(a),32+r*Math.sin(a)):ctx.lineTo(32+r*Math.cos(a),32+r*Math.sin(a));}'
          'ctx.closePath();ctx.fill();'
          'ctx.fillStyle="rgba(255,255,255,0.60)";ctx.beginPath();ctx.arc(32,32,28,0,Math.PI*2);ctx.fill();'
          'ctx.strokeStyle="#7a1f1f";ctx.lineWidth=5.5;ctx.fillStyle="#7a1f1f";'
          'ctx.beginPath();ctx.arc(32,32,22,0,Math.PI*2);ctx.stroke();'
          'ctx.beginPath();ctx.arc(32,32,9,0,Math.PI*2);ctx.fill();'
        '});'

        # city — white backing + outer ring + filled inner dot (crimson)
        '_mk("cat-city",function(ctx){'
          'ctx.fillStyle="rgba(255,255,255,0.60)";ctx.beginPath();ctx.arc(32,32,28,0,Math.PI*2);ctx.fill();'
          'ctx.strokeStyle="#7a1f1f";ctx.lineWidth=5.5;ctx.fillStyle="#7a1f1f";'
          'ctx.beginPath();ctx.arc(32,32,22,0,Math.PI*2);ctx.stroke();'
          'ctx.beginPath();ctx.arc(32,32,9,0,Math.PI*2);ctx.fill();'
        '});'

        # town — white backing + open ring (no inner dot distinguishes from city)
        '_mk("cat-town",function(ctx){'
          'ctx.fillStyle="rgba(255,255,255,0.60)";ctx.beginPath();ctx.arc(32,32,22,0,Math.PI*2);ctx.fill();'
          'ctx.strokeStyle="#7a1f1f";ctx.lineWidth=5.5;'
          'ctx.beginPath();ctx.arc(32,32,16,0,Math.PI*2);ctx.stroke();'
        '});'

        # route-node / caravanserai — white backing + diamond outline + inner dot
        '_mk("cat-route-node",function(ctx){'
          'ctx.fillStyle="rgba(255,255,255,0.60)";ctx.beginPath();ctx.moveTo(32,1);ctx.lineTo(63,32);ctx.lineTo(32,63);ctx.lineTo(1,32);ctx.closePath();ctx.fill();'
          'ctx.strokeStyle="#7a1f1f";ctx.lineWidth=6.0;ctx.fillStyle="#7a1f1f";'
          'ctx.beginPath();ctx.moveTo(32,5);ctx.lineTo(59,32);ctx.lineTo(32,59);ctx.lineTo(5,32);ctx.closePath();ctx.stroke();'
          'ctx.beginPath();ctx.arc(32,32,7,0,Math.PI*2);ctx.fill();'
        '});'

        # sacred-site — eye/nazar; white sclera, teal iris, dark pupil (unique color)
        '_mk("cat-sacred-site",function(ctx){'
          'ctx.beginPath();ctx.moveTo(6,32);'
          'ctx.bezierCurveTo(20,10,44,10,58,32);'
          'ctx.bezierCurveTo(44,54,20,54,6,32);'
          'ctx.closePath();'
          'ctx.fillStyle="rgba(255,255,255,0.60)";ctx.fill();'
          'ctx.strokeStyle="#0a4040";ctx.lineWidth=4.0;ctx.stroke();'
          'ctx.fillStyle="#1a7a7a";ctx.beginPath();ctx.arc(32,32,13,0,Math.PI*2);ctx.fill();'
          'ctx.fillStyle="#0a3030";ctx.beginPath();ctx.arc(32,32,6,0,Math.PI*2);ctx.fill();'
          'ctx.fillStyle="rgba(255,255,255,0.60)";ctx.beginPath();ctx.arc(36,27,3,0,Math.PI*2);ctx.fill();'
        '});'

        # fortress — heraldic shield; white backing, crimson fill, gold boss
        '_mk("cat-fortress",function(ctx){'
          'ctx.fillStyle="rgba(255,255,255,0.60)";'
          'ctx.beginPath();ctx.moveTo(9,8);ctx.lineTo(55,8);ctx.lineTo(55,34);'
          'ctx.quadraticCurveTo(55,56,32,62);ctx.quadraticCurveTo(9,56,9,34);'
          'ctx.closePath();ctx.fill();'
          'ctx.fillStyle="#7a1f1f";'
          'ctx.beginPath();ctx.moveTo(12,11);ctx.lineTo(52,11);ctx.lineTo(52,34);'
          'ctx.quadraticCurveTo(52,52,32,58);ctx.quadraticCurveTo(12,52,12,34);'
          'ctx.closePath();ctx.fill();'
          'ctx.strokeStyle="#b8892a";ctx.lineWidth=3.0;ctx.stroke();'
          'ctx.fillStyle="#b8892a";ctx.beginPath();ctx.arc(32,32,6,0,Math.PI*2);ctx.fill();'
        '});'

        # oasis — white backing + two concentric rings; gold outer, crimson inner
        '_mk("cat-oasis",function(ctx){'
          'ctx.fillStyle="rgba(255,255,255,0.60)";ctx.beginPath();ctx.arc(32,32,28,0,Math.PI*2);ctx.fill();'
          'ctx.strokeStyle="#b8892a";ctx.lineWidth=6.0;'
          'ctx.beginPath();ctx.arc(32,32,22,0,Math.PI*2);ctx.stroke();'
          'ctx.strokeStyle="#7a1f1f";ctx.lineWidth=5.0;'
          'ctx.beginPath();ctx.arc(32,32,12,0,Math.PI*2);ctx.stroke();'
          'ctx.fillStyle="#b8892a";'
          'ctx.beginPath();ctx.arc(32,32,4,0,Math.PI*2);ctx.fill();'
        '});'

        # landmark — clean triangle mountain, gold peak cap, no curves
        '_mk("cat-landmark",function(ctx){'
          'ctx.fillStyle="rgba(255,255,255,0.60)";'
          'ctx.beginPath();ctx.moveTo(3,61);ctx.lineTo(32,3);ctx.lineTo(61,61);ctx.closePath();ctx.fill();'
          'ctx.fillStyle="#7a1f1f";'
          'ctx.beginPath();ctx.moveTo(6,58);ctx.lineTo(32,7);ctx.lineTo(58,58);ctx.closePath();ctx.fill();'
          'ctx.strokeStyle="#b8892a";ctx.lineWidth=3.5;ctx.stroke();'
          'ctx.fillStyle="#b8892a";'
          'ctx.beginPath();ctx.moveTo(20,38);ctx.lineTo(32,7);ctx.lineTo(44,38);ctx.closePath();ctx.fill();'
        '});'

        # lake — concentric blue ripple rings, light→dark toward center
        '_mk("cat-lake",function(ctx){'
          'ctx.fillStyle="rgba(255,255,255,0.60)";ctx.beginPath();ctx.arc(32,32,28,0,Math.PI*2);ctx.fill();'
          'ctx.strokeStyle="#6aaed6";ctx.lineWidth=3.5;ctx.beginPath();ctx.arc(32,32,22,0,Math.PI*2);ctx.stroke();'
          'ctx.strokeStyle="#2e7fb8";ctx.lineWidth=4.0;ctx.beginPath();ctx.arc(32,32,14,0,Math.PI*2);ctx.stroke();'
          'ctx.strokeStyle="#1a5a90";ctx.lineWidth=4.5;ctx.beginPath();ctx.arc(32,32,7,0,Math.PI*2);ctx.stroke();'
          'ctx.fillStyle="#1a5a90";ctx.beginPath();ctx.arc(32,32,3,0,Math.PI*2);ctx.fill();'
        '});'

        # poi — teardrop pin: circle top + wedge, white hole in center
        '_mk("cat-poi",function(ctx){'
          'ctx.fillStyle="rgba(255,255,255,0.60)";'
          'ctx.beginPath();ctx.arc(32,21,18,0,Math.PI*2);ctx.fill();'
          'ctx.beginPath();ctx.moveTo(18,28);ctx.lineTo(32,62);ctx.lineTo(46,28);ctx.closePath();ctx.fill();'
          'ctx.fillStyle="#7a1f1f";'
          'ctx.beginPath();ctx.arc(32,21,14,0,Math.PI*2);ctx.fill();'
          'ctx.beginPath();ctx.moveTo(22,28);ctx.lineTo(32,58);ctx.lineTo(42,28);ctx.closePath();ctx.fill();'
          'ctx.fillStyle="rgba(255,255,255,0.60)";ctx.beginPath();ctx.arc(32,21,6,0,Math.PI*2);ctx.fill();'
        '});'

        # dungeon / ruins — white backing + broken arc + inner dot
        '_mk("cat-dungeon",function(ctx){'
          'ctx.fillStyle="rgba(255,255,255,0.60)";ctx.beginPath();ctx.arc(32,32,28,0,Math.PI*2);ctx.fill();'
          'ctx.strokeStyle="#5a4020";ctx.lineWidth=6.0;ctx.lineCap="round";'
          'ctx.beginPath();ctx.arc(32,32,22,0,Math.PI*1.5,false);ctx.stroke();'
          'ctx.fillStyle="#5a4020";'
          'ctx.beginPath();ctx.arc(32,32,8,0,Math.PI*2);ctx.fill();'
        '});'

        '})();\n'
    )
