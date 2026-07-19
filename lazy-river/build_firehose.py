from _shared import page, static_waterfall_bar

EXTRA_STYLE = """<style>
  @keyframes fhSpray {
    0% { stroke-dashoffset: 0; }
    100% { stroke-dashoffset: -40; }
  }
  .fh-stage { position: relative; max-width: 640px; margin: 0 auto; background: linear-gradient(180deg, #0a3350 0%, #04182b 100%); border: 4px ridge #00ffff; padding: 10px; }
  .fh-hose-wrap { position: relative; width: 100%; height: 380px; cursor: pointer; user-select: none; overflow: hidden; }
  .fh-hose {
    position: absolute; bottom: 10px; left: 50%; transform-origin: bottom center; transform: translateX(-50%) rotate(0deg);
    width: 90px; transition: transform 0.15s ease-out;
  }
  .fh-spray { position: absolute; bottom: 60px; left: 50%; transform-origin: bottom center; pointer-events: none; }
  .fh-spray.on { display: block; }
  .fh-spray.off { display: none; }
  .fh-target { position: absolute; font-size: 40px; transition: top 0.2s, left 0.2s, opacity 0.3s; }
  .fh-target.hit { opacity: 0; }
  .fh-meter { background: #001a33; border: 3px inset #0099cc; height: 22px; width: 100%; margin: 8px 0; position: relative; }
  .fh-meter-fill { background: linear-gradient(90deg, #00ccff, #66e0ff); height: 100%; width: 0%; transition: width 0.1s; }
  .fh-score { text-align: center; font-family: "Courier New", monospace; color: #ffff00; font-size: 20px; font-weight: bold; }
</style>"""

content = f"""
    <center><font face="Arial Black, Impact" size="7" color="#ffff00"><b class="blk">&#128167; TAP THE FIREHOSE &#128167;</b></font></center>
    <center><font face="Courier New, monospace" size="3" color="#00ffff">click and hold to spray &middot; aim with your mouse &middot; soak the targets before the tank runs dry</font></center>

    {static_waterfall_bar("HOSE STATION")}

    <div class="fh-stage">
      <div class="fh-score">SOAKED: <span id="fhScore">0</span> &nbsp;|&nbsp; TANK: <span id="fhTankPct">100</span>%</div>
      <div class="fh-meter"><div class="fh-meter-fill" id="fhMeterFill"></div></div>
      <div class="fh-hose-wrap" id="fhStageArea">
        <span class="fh-target" id="fhT0" style="top:10%;left:15%;">&#127754;</span>
        <span class="fh-target" id="fhT1" style="top:20%;left:70%;">&#128293;</span>
        <span class="fh-target" id="fhT2" style="top:45%;left:35%;">&#127754;</span>
        <span class="fh-target" id="fhT3" style="top:15%;left:85%;">&#128293;</span>
        <span class="fh-target" id="fhT4" style="top:55%;left:8%;">&#127754;</span>

        <svg class="fh-spray off" id="fhSpray" width="10" height="260" viewBox="0 0 10 260">
          <line x1="5" y1="0" x2="5" y2="260" stroke="#aeeeff" stroke-width="6" stroke-dasharray="10 8" opacity="0.85">
            <animate attributeName="stroke-dashoffset" from="0" to="-36" dur="0.25s" repeatCount="indefinite"/>
          </line>
        </svg>

        <div class="fh-hose" id="fhHose">
          <svg width="90" height="60" viewBox="0 0 90 60">
            <rect x="0" y="30" width="60" height="16" fill="#8a3b1a" rx="4"/>
            <rect x="55" y="20" width="24" height="30" fill="#c0c0c0" rx="4" stroke="#333" stroke-width="2"/>
            <circle cx="70" cy="35" r="6" fill="#333"/>
          </svg>
        </div>
      </div>
      <center><button id="fhRefill" type="button" style="margin-top:8px;background:#003366;color:#00ffff;border:2px outset #0099cc;padding:6px 16px;font-weight:bold;cursor:pointer;">REFILL TANK</button></center>
    </div>

    {static_waterfall_bar("NINJA WATCH")}
    <font color="#fff" face="Arial, Helvetica, sans-serif" size="2">
    <p>Local reports indicate several ninjas have taken up residence near the hose station. They do not
    appear to be hostile. They do not appear to be doing anything, actually. They're just kind of bobbing
    there. MEGAVISION Legal has advised us this is fine.</p>
    </font>
"""

extra_script = """
<script>
(function() {
  var hose = document.getElementById('fhHose');
  var spray = document.getElementById('fhSpray');
  var stage = document.getElementById('fhStageArea');
  var scoreEl = document.getElementById('fhScore');
  var tankPctEl = document.getElementById('fhTankPct');
  var meterFill = document.getElementById('fhMeterFill');
  var refillBtn = document.getElementById('fhRefill');
  var targets = [0,1,2,3,4].map(function(i) { return document.getElementById('fhT' + i); });
  var score = 0, tank = 100, spraying = false, drainTimer = null;

  function updateHUD() {
    scoreEl.textContent = score;
    tankPctEl.textContent = Math.max(0, Math.round(tank));
    meterFill.style.width = Math.max(0, tank) + '%';
  }

  function aimAt(clientX, clientY) {
    var rect = stage.getBoundingClientRect();
    var hoseX = rect.left + rect.width / 2;
    var hoseY = rect.bottom - 20;
    var dx = clientX - hoseX;
    var dy = clientY - hoseY;
    var angle = Math.atan2(dx, -dy) * (180 / Math.PI);
    angle = Math.max(-80, Math.min(80, angle));
    hose.style.transform = 'translateX(-50%) rotate(' + angle + 'deg)';
    spray.style.transform = 'translateX(-50%) rotate(' + angle + 'deg)';

    var len = Math.min(260, Math.hypot(dx, dy));
    spray.setAttribute('height', len);
    spray.setAttribute('viewBox', '0 0 10 ' + len);
    spray.querySelector('line').setAttribute('y2', len);

    checkHits(hoseX, hoseY, angle, len);
  }

  function checkHits(hoseX, hoseY, angle, len) {
    var rad = angle * Math.PI / 180;
    var tipX = hoseX + Math.sin(rad) * len;
    var tipY = hoseY - Math.cos(rad) * len;
    targets.forEach(function(t) {
      if (t.classList.contains('hit')) return;
      var r = t.getBoundingClientRect();
      var cx = r.left + r.width / 2;
      var cy = r.top + r.height / 2;
      if (Math.hypot(tipX - cx, tipY - cy) < 45) {
        t.classList.add('hit');
        score += 10;
        setTimeout(function() { respawn(t); }, 900 + Math.random() * 800);
      }
    });
  }

  function respawn(t) {
    t.style.top = (5 + Math.random() * 70) + '%';
    t.style.left = (5 + Math.random() * 80) + '%';
    t.classList.remove('hit');
  }

  function startSpray() {
    if (tank <= 0) return;
    spraying = true;
    spray.classList.remove('off');
    spray.classList.add('on');
    if (drainTimer) clearInterval(drainTimer);
    drainTimer = setInterval(function() {
      tank -= 1.4;
      if (tank <= 0) { tank = 0; stopSpray(); }
      updateHUD();
    }, 120);
  }
  function stopSpray() {
    spraying = false;
    spray.classList.remove('on');
    spray.classList.add('off');
    if (drainTimer) { clearInterval(drainTimer); drainTimer = null; }
  }

  stage.addEventListener('mousedown', function(e) { startSpray(); aimAt(e.clientX, e.clientY); });
  window.addEventListener('mouseup', stopSpray);
  stage.addEventListener('mousemove', function(e) { if (spraying) aimAt(e.clientX, e.clientY); });
  stage.addEventListener('touchstart', function(e) { startSpray(); var t = e.touches[0]; aimAt(t.clientX, t.clientY); }, { passive: true });
  stage.addEventListener('touchmove', function(e) { if (spraying) { var t = e.touches[0]; aimAt(t.clientX, t.clientY); } }, { passive: true });
  window.addEventListener('touchend', stopSpray);

  refillBtn.addEventListener('click', function() { tank = 100; updateHUD(); });

  updateHUD();
})();
</script>
"""

page("firehose.html", "Tap The Firehose", content + extra_script, extra_head=EXTRA_STYLE)

print("done: firehose.html")
