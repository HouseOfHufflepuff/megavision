from _shared import page, static_waterfall_bar, showcase_carousel

content = f"""
    <center><font face="Arial Black, Impact" size="7" color="#ffff00"><b class="blk">&#127754; THE LAZY RIVER OUTPOST &#127754;</b></font></center>
    <center><font face="Courier New, monospace" size="4" color="#00ffff">40+ pages of obsessive lazy river content, because someone had to do it</font></center>

    {showcase_carousel("lrvShowcaseHome")}

    {static_waterfall_bar("WHAT'S HERE")}
    <font color="#fff" face="Arial, Helvetica, sans-serif" size="2">
    <p>This sub-site is MEGAVISION's complete, unreasonably thorough guide to lazy rivers: a researched,
    sourced ranking of the ten longest lazy rivers on Earth, a (joke) shop where you can "rent" a lazy
    river for your event, a fully playable firehose minigame, and enough supplementary guide pages about
    tube etiquette and current physics to make you the most insufferable person at any water park.</p>
    </font>

    {static_waterfall_bar("WHERE TO START")}
    <table width="100%" cellpadding="0" cellspacing="0"><tr>
      <td width="33%" align="center" valign="top" style="padding:8px;">
        <table bgcolor="#001a33" border="2" cellpadding="10" style="border-color:#0099cc;">
        <tr><td align="center">
          <font size="6">&#127942;</font><br>
          <font color="#ffff00" size="3"><b>Top 10 Longest Rivers</b></font><br>
          <font color="#fff" size="2">Ranked, sourced, and mildly argued about.</font><br><br>
          <a href="top-10.html"><font color="#00ffff" size="2">SEE THE RANKING &rarr;</font></a>
        </td></tr></table>
      </td>
      <td width="33%" align="center" valign="top" style="padding:8px;">
        <table bgcolor="#001a33" border="2" cellpadding="10" style="border-color:#0099cc;">
        <tr><td align="center">
          <font size="6">&#128176;</font><br>
          <font color="#ffff00" size="3"><b>Rent-A-River Shop</b></font><br>
          <font color="#fff" size="2">Bar mitzvahs. Pride. Quinceañeras. LAN parties. Petting zoos. We've thought about all of it.</font><br><br>
          <a href="shop.html"><font color="#00ffff" size="2">VISIT THE SHOP &rarr;</font></a>
        </td></tr></table>
      </td>
      <td width="33%" align="center" valign="top" style="padding:8px;">
        <table bgcolor="#001a33" border="2" cellpadding="10" style="border-color:#0099cc;">
        <tr><td align="center">
          <font size="6">&#128167;</font><br>
          <font color="#ffff00" size="3"><b>Tap The Firehose</b></font><br>
          <font color="#fff" size="2">A fully playable minigame. There are ninjas. Don't ask.</font><br><br>
          <a href="firehose.html"><font color="#00ffff" size="2">SPRAY SOMETHING &rarr;</font></a>
        </td></tr></table>
      </td>
    </tr></table>

    {static_waterfall_bar("THE FULL GUIDE")}
    <font color="#fff" face="Arial, Helvetica, sans-serif" size="2">
    Use the &#9776; RIVER MENU on the left for everything else -- history, engineering, tube types, safety,
    world records, regional roundups (USA / Europe / Asia), pop culture appearances, three photo galleries,
    FAQ, links, and a guestbook, because it's not a real 90s fansite without a guestbook.
    </font>
"""

page("index.html", "Home", content)
print("done: index.html")
