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
        # _mk draws at 64×64 and registers at pixelRatio:2 (32 logical px, @2x sharp)
        'function _mk(name,draw){var c=document.createElement("canvas");c.width=64;c.height=64;var ctx=c.getContext("2d");draw(ctx);var d=ctx.getImageData(0,0,64,64);map.addImage(name,{width:64,height:64,data:d.data},{pixelRatio:2});}'

        # city — thin outer ring + filled inner dot (crimson); the canonical "major settlement"
        '_mk("cat-city",function(ctx){'
          'ctx.strokeStyle="#7a1f1f";ctx.lineWidth=2.5;ctx.fillStyle="#7a1f1f";'
          'ctx.beginPath();ctx.arc(32,32,20,0,Math.PI*2);ctx.stroke();'
          'ctx.beginPath();ctx.arc(32,32,7,0,Math.PI*2);ctx.fill();'
        '});'

        # town — open ring, smaller radius than city (no inner dot distinguishes from city);
        # radius kept proportional to MapTiler's own city:town native sprite ratio (21px:13px)
        '_mk("cat-town",function(ctx){'
          'ctx.strokeStyle="#7a1f1f";ctx.lineWidth=2.5;'
          'ctx.beginPath();ctx.arc(32,32,13,0,Math.PI*2);ctx.stroke();'
        '});'

        # route-node / caravanserai — diamond outline + inner dot (waypoint convention)
        '_mk("cat-route-node",function(ctx){'
          'ctx.strokeStyle="#7a1f1f";ctx.lineWidth=2.5;ctx.fillStyle="#7a1f1f";'
          'ctx.beginPath();ctx.moveTo(32,4);ctx.lineTo(60,32);ctx.lineTo(32,60);ctx.lineTo(4,32);ctx.closePath();ctx.stroke();'
          'ctx.beginPath();ctx.arc(32,32,7,0,Math.PI*2);ctx.fill();'
        '});'

        # sacred-site — arch/dome silhouette (Silk Road mosque/shrine form); gold fill, crimson outline
        '_mk("cat-sacred-site",function(ctx){'
          'ctx.beginPath();ctx.moveTo(14,58);ctx.lineTo(14,34);'
          'ctx.quadraticCurveTo(14,6,32,6);ctx.quadraticCurveTo(50,6,50,34);'
          'ctx.lineTo(50,58);ctx.closePath();'
          'ctx.fillStyle="rgba(184,137,42,0.25)";ctx.fill();'
          'ctx.strokeStyle="#7a1f1f";ctx.lineWidth=2.5;ctx.stroke();'
          'ctx.beginPath();ctx.moveTo(14,58);ctx.lineTo(50,58);'
          'ctx.strokeStyle="#b8892a";ctx.lineWidth=2.0;ctx.stroke();'
        '});'

        # fortress — crenellated battlement plan (universal castle/fort symbol)
        '_mk("cat-fortress",function(ctx){'
          'ctx.beginPath();'
          'ctx.moveTo(8,16);ctx.lineTo(20,16);ctx.lineTo(20,32);ctx.lineTo(26,32);'
          'ctx.lineTo(26,16);ctx.lineTo(38,16);ctx.lineTo(38,32);ctx.lineTo(44,32);'
          'ctx.lineTo(44,16);ctx.lineTo(56,16);ctx.lineTo(56,56);ctx.lineTo(8,56);ctx.closePath();'
          'ctx.fillStyle="#7a1f1f";ctx.fill();'
          'ctx.strokeStyle="#b8892a";ctx.lineWidth=2.5;ctx.stroke();'
        '});'

        # oasis — two concentric rings (water ripple/source convention); gold outer, crimson inner
        '_mk("cat-oasis",function(ctx){'
          'ctx.strokeStyle="#b8892a";ctx.lineWidth=2.5;'
          'ctx.beginPath();ctx.arc(32,32,22,0,Math.PI*2);ctx.stroke();'
          'ctx.strokeStyle="#7a1f1f";ctx.lineWidth=2.5;'
          'ctx.beginPath();ctx.arc(32,32,12,0,Math.PI*2);ctx.stroke();'
          'ctx.fillStyle="#b8892a";'
          'ctx.beginPath();ctx.arc(32,32,4,0,Math.PI*2);ctx.fill();'
        '});'

        # landmark — mountain silhouette (universal topographic convention)
        '_mk("cat-landmark",function(ctx){'
          'ctx.beginPath();ctx.moveTo(4,56);'
          'ctx.quadraticCurveTo(10,28,22,24);ctx.quadraticCurveTo(28,12,34,24);'
          'ctx.quadraticCurveTo(44,28,60,56);ctx.closePath();'
          'ctx.fillStyle="#7a1f1f";ctx.fill();'
          'ctx.strokeStyle="#b8892a";ctx.lineWidth=2.5;ctx.stroke();'
        '});'

        # poi — small filled dot (generic unclassified point)
        '_mk("cat-poi",function(ctx){'
          'ctx.fillStyle="#7a1f1f";'
          'ctx.beginPath();ctx.arc(32,32,10,0,Math.PI*2);ctx.fill();'
        '});'

        # dungeon / ruins — partial arc (270°, gap at upper-right) + inner dot;
        # the broken ring reads as "place, but damaged/abandoned"
        '_mk("cat-dungeon",function(ctx){'
          'ctx.strokeStyle="#5a4020";ctx.lineWidth=2.5;ctx.lineCap="round";'
          'ctx.beginPath();ctx.arc(32,32,22,0,Math.PI*1.5,false);ctx.stroke();'
          'ctx.fillStyle="#5a4020";'
          'ctx.beginPath();ctx.arc(32,32,6,0,Math.PI*2);ctx.fill();'
        '});'

        '})();\n'
    )
