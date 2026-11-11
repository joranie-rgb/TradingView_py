"""Generate hosted Pine checks from the current production sources.

Run from any directory. Fixtures place emulator orders only; never connect them
to alerts or a broker. The source digest makes the tested revision explicit.
"""
from pathlib import Path
import hashlib
import re

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def helper(source, name):
    match = re.search(rf"^{name}\([^\n]*\) =>\n(?:    [^\n]*\n)+", source, re.M)
    if not match:
        raise ValueError(f"Missing source helper: {name}")
    return match.group()


def build():
    indicator = (ROOT / "liquidity_structure_v1.pine").read_text(encoding="utf-8")
    strategy = (ROOT / "futures_v7_5.pine").read_text(encoding="utf-8")
    digest = lambda text: hashlib.sha256(text.encode()).hexdigest()
    indicator_digest = digest(indicator)
    indicator = indicator.replace('indicator("Liquidity + Structure Monitor v1.1", shorttitle = "LSM v1.1"',
                                  'indicator("HOSTED Indicator lifecycle audit", shorttitle = "HOSTED LSM"', 1)
    anchor = "// Values above describe the setup entering this bar."
    if indicator.count(anchor) != 1:
        raise ValueError("Indicator transition anchor changed")
    indicator = indicator.replace(anchor, '''int auditPriorDirection = armedDirection
float auditPriorBreak = breakLevel
line auditPriorLine = armedLine
''' + anchor)
    indicator += "\n// Production source SHA256: " + indicator_digest + "\n"
    indicator += '''
// Assertions observe the full production state machine above on actual OHLC.
var int auditArms = 0
var int auditSignals = 0
var int auditCancels = 0
var int auditSessionRejects = 0
if barstate.isconfirmed
    bool newArm = armedLongNow or armedShortNow
    bool signal = longSignal or shortSignal
    if newArm
        auditArms += 1
        if signal or armedBar != bar_index or armedLine == auditPriorLine
            runtime.error("AUDIT: same-bar signal or drawing reuse")
        if line.get_y1(armedLine) != breakLevel or line.get_y2(armedLine) != breakLevel
            runtime.error("AUDIT: frozen line does not match structure")
    if signal
        auditSignals += 1
        if auditPriorDirection == 0 or pendingCancellation != "" or not inSession or crossesCalendarDate
            runtime.error("AUDIT: signal bypassed lifecycle gates")
        if (longSignal ? referenceTarget - referenceEntry : referenceEntry - referenceTarget) < tick * 0.999
            runtime.error("AUDIT: target below one favorable tick")
    if auditPriorDirection != 0 and pendingCancellation != ""
        auditCancels += 1
        if signal
            runtime.error("AUDIT: cancellation lost priority")
    if not inSession or crossesCalendarDate
        auditSessionRejects += 1
        if newArm or signal or armedDirection != 0
            runtime.error("AUDIT: session/date exclusion bypassed")
    if auditPriorDirection != 0 and pendingCancellation == "" and not signal and not newArm
        if breakLevel != auditPriorBreak
            runtime.error("AUDIT: frozen level moved")
if barstate.isfirst
    if sessionWindowEnd(timestamp(zone, 2026, 11, 10, 10, 0), "0930-1600", zone) != timestamp(zone, 2026, 11, 10, 16, 0)
        runtime.error("AUDIT: hourly session alignment")
    if sessionWindowEnd(timestamp(zone, 2026, 12, 31, 23, 0), "1800-0500", zone) != timestamp(zone, 2027, 1, 1, 5, 0)
        runtime.error("AUDIT: overnight year boundary")
    if setupInvalidated(1, 95, 101, 95) or not setupInvalidated(1, 94.75, 101, 95)
        runtime.error("AUDIT: equal touch versus breach")
    if setupCancellation(true, false, true, true) != "SWEEP EXTREME BROKEN"
        runtime.error("AUDIT: invalidation/expiry priority")
    if setupCancellation(true, false, false, true) != "SETUP EXPIRED"
        runtime.error("AUDIT: expiry")
    if setupCancellation(true, true, false, false) != "SESSION RESET"
        runtime.error("AUDIT: date reset")
    int midnight = timestamp(zone, 2026, 11, 11, 0, 0)
    if calendarDate(midnight - 1) == calendarDate(midnight)
        runtime.error("AUDIT: midnight classification")
    int spring = timestamp(zone, 2026, 3, 9, 0, 0) - timestamp(zone, 2026, 3, 8, 0, 0)
    int autumn = timestamp(zone, 2026, 11, 2, 0, 0) - timestamp(zone, 2026, 11, 1, 0, 0)
    if zone == "America/New_York" and (spring != 23 * 3600000 or autumn != 25 * 3600000)
        runtime.error("AUDIT: DST calendar lengths")
var table audit = table.new(position.bottom_left, 2, 5, bgcolor = color.black)
if barstate.islastconfirmedhistory or barstate.islast
    table.cell(audit, 0, 0, "HOSTED ASSERTIONS", text_color = color.white)
    table.cell(audit, 1, 0, auditArms > 0 and auditSignals > 0 and auditCancels > 0 ? "PASS" : "INCOMPLETE COVERAGE", text_color = color.lime)
    table.cell(audit, 0, 1, "Arms", text_color = color.white)
    table.cell(audit, 1, 1, str.tostring(auditArms), text_color = color.white)
    table.cell(audit, 0, 2, "Signals", text_color = color.white)
    table.cell(audit, 1, 2, str.tostring(auditSignals), text_color = color.white)
    table.cell(audit, 0, 3, "Cancellations", text_color = color.white)
    table.cell(audit, 1, 3, str.tostring(auditCancels), text_color = color.white)
    table.cell(audit, 0, 4, "Excluded bars", text_color = color.white)
    table.cell(audit, 1, 4, str.tostring(auditSessionRejects), text_color = color.white)
'''
    (OUT / "indicator_lifecycle.pine").write_text(indicator, encoding="utf-8")
    names = ("riskDayStamp", "dayChanged", "fullPositionExit", "freshEntry", "dailyBaseline")
    accounting = '''//@version=6
strategy("HOSTED Accounting reconciliation", shorttitle="HOSTED Ledger", overlay=true,
 initial_capital=500000, currency=currency.USD, pyramiding=0,
 commission_type=strategy.commission.cash_per_contract, commission_value=2.5,
 slippage=1, process_orders_on_close=true, calc_on_order_fills=false,
 calc_on_every_tick=false, margin_long=100, margin_short=100)
string sessionTimezone = "America/New_York"
int anchor = input.time(timestamp("10 Nov 2026 23:57 -0500"), "First order bar open")
if barstate.isfirst and timeframe.in_seconds() != 60
    runtime.error("Use standard MNQ one-minute ETH candles")
'''
    accounting += "\n".join(helper(strategy, name) for name in names)
    accounting += '''
int currentRiskDay = riskDayStamp(time)
bool newRiskDay = dayChanged(currentRiskDay, currentRiskDay[1])
'''
    # Exact production observation/reset/counting block, not a Python substitute.
    start = strategy.index("bool newPositionOpened =")
    end = strategy.index("float dailyRealizedPnl =", start)
    block = strategy[start:end]
    accounting += block
    accounting += '''
int step = int((time - anchor) / 60000)
var int entriesObserved = 0
var int fullExitsObserved = 0
var int partialExitsObserved = 0
var int plan = na
if newlyObservedEntry
    entriesObserved += 1
if positionJustClosed
    fullExitsObserved += 1
    plan := na
if closedTradeChange > 0 and strategy.position_size != 0
    partialExitsObserved += 1
    if na(plan) or positionJustClosed
        runtime.error("AUDIT: partial exit destroyed plan")
if time >= anchor and step <= 5
    float expectedSize = step == 1 ? 3 : step == 2 ? 2 : step == 4 ? 2 : 0
    if strategy.position_size != expectedSize
        runtime.error("AUDIT: wrong observed position at step " + str.tostring(step))
    if step == 2 and not na(lastExitBar)
        runtime.error("AUDIT: partial exit started full-exit cooldown")
    if step == 3 and lastExitBar != bar_index
        runtime.error("AUDIT: full exit did not start cooldown")
    if step == 3 and (dayStartingEquity != strategy.equity[1] or dayStartingNetProfit != strategy.netprofit[1])
        runtime.error("AUDIT: reset lost previous valuation baseline")
    if step == 3 and tradesToday != 0
        runtime.error("AUDIT: old entry recounted after midnight")
    if step == 4 and tradesToday != 1
        runtime.error("AUDIT: fresh entry not counted in new day")
if time == anchor
    plan := 100000
    strategy.entry("Audit", strategy.long, qty=3)
    strategy.exit("Protection", "Audit", loss=plan, profit=plan)
if time == anchor + 60000
    strategy.close("Audit", qty=1, immediately=true, comment="Partial one")
if time == anchor + 120000
    strategy.close("Audit", immediately=true, comment="Full remainder")
if time == anchor + 180000
    plan := 100000
    strategy.entry("Audit", strategy.long, qty=2)
    strategy.exit("Protection", "Audit", loss=plan, profit=plan)
if time == anchor + 240000
    strategy.close("Audit", immediately=true, comment="Full second")
float gross = 0
float fees = 0
if strategy.closedtrades > 0
    for i = 0 to strategy.closedtrades - 1
        gross += (strategy.closedtrades.exit_price(i) - strategy.closedtrades.entry_price(i)) * strategy.closedtrades.size(i) * syminfo.pointvalue
        fees += strategy.closedtrades.commission(i)
bool complete = time >= anchor + 300000 and entriesObserved == 2 and fullExitsObserved == 2 and partialExitsObserved == 1 and strategy.closedtrades == 3
if complete and (math.abs(gross - fees - strategy.netprofit) > 0.01 or math.abs(fees - 25) > 0.01)
    runtime.error("AUDIT: fill-price/commission ledger mismatch")
var table audit = table.new(position.top_right, 2, 7, bgcolor=color.black)
if barstate.islastconfirmedhistory or barstate.islast
    table.cell(audit, 0, 0, "HOSTED LEDGER", text_color=color.white)
    table.cell(audit, 1, 0, complete ? "PASS" : "INCOMPLETE", text_color=color.lime)
    table.cell(audit, 0, 1, "Entries / partial / full", text_color=color.white)
    table.cell(audit, 1, 1, str.tostring(entriesObserved)+" / "+str.tostring(partialExitsObserved)+" / "+str.tostring(fullExitsObserved), text_color=color.white)
    table.cell(audit, 0, 2, "Closed records", text_color=color.white)
    table.cell(audit, 1, 2, str.tostring(strategy.closedtrades), text_color=color.white)
    table.cell(audit, 0, 3, "Gross from fills", text_color=color.white)
    table.cell(audit, 1, 3, str.tostring(gross,"#.00"), text_color=color.white)
    table.cell(audit, 0, 4, "Commission", text_color=color.white)
    table.cell(audit, 1, 4, str.tostring(fees,"#.00"), text_color=color.white)
    table.cell(audit, 0, 5, "Net from fills", text_color=color.white)
    table.cell(audit, 1, 5, str.tostring(gross-fees,"#.00"), text_color=color.white)
    table.cell(audit, 0, 6, "Emulator net", text_color=color.white)
    table.cell(audit, 1, 6, str.tostring(strategy.netprofit,"#.00"), text_color=color.white)
'''
    accounting = accounting.replace('int currentRiskDay =', '// Production source SHA256: ' + digest(strategy) + '\nint currentRiskDay =', 1)
    (OUT / "accounting_reconciliation.pine").write_text(accounting, encoding="utf-8")
    print("Generated hosted fixtures from", digest(strategy), digest((ROOT / 'liquidity_structure_v1.pine').read_text(encoding='utf-8')))


if __name__ == "__main__":
    build()
