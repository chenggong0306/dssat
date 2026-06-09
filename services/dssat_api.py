import json, math, os, re, shutil, subprocess, threading, time, uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = os.environ.get("DSSAT_ROOT", r"C:\DSSAT48")
EXE = os.environ.get("DSSAT_EXE") or os.path.join(ROOT, "DSCSM048.EXE")
if not os.path.exists(EXE):
    linux_exe = os.path.join(ROOT, "dscsm048")
    if os.path.exists(linux_exe):
        EXE = linux_exe
RUNS = os.path.abspath(os.environ.get("DSSAT_RUNS", "runs"))
LOCK = threading.Lock()
CROPS = {
    "maize": {"model": "MZCER048", "directory": "Maize", "fileExt": "MZX", "cropCode": "MZ", "defaultCultivar": "990002", "yieldProduct": "grain", "status": "supported", "plantingMethod": "S", "plantingDistribution": "R", "pop": 6.75, "row": 65, "plantDepth": 5, "plantWeight": -99, "sprl": 0, "symbi": "N", "photo": "R"},
    "soybean": {"model": "CRGRO048", "directory": "Soybean", "fileExt": "SBX", "cropCode": "SB", "defaultCultivar": "IB0055", "yieldProduct": "grain", "status": "planned", "note": "Current DSSAT48 soybean sample files fail with IPEXP STOP 99 in this runtime; keep planned until module/data mapping is fixed.", "plantingMethod": "S", "plantingDistribution": "R", "pop": 16, "row": 45, "plantDepth": 3, "plantWeight": -99, "sprl": -99, "symbi": "Y", "photo": "L"},
    "rice": {"model": "RICER048", "directory": "Rice", "fileExt": "RIX", "cropCode": "RI", "defaultCultivar": "IB0055", "yieldProduct": "grain", "status": "supported", "plantingMethod": "T", "plantingDistribution": "H", "pop": 25, "row": 22, "plantDepth": 5, "plantWeight": 0, "page": 30, "penv": 25, "plph": 1, "sprl": -99, "symbi": "N", "photo": "C"},
    "wheat": {"model": "WHAPS048", "directory": "Wheat", "fileExt": "WHX", "cropCode": "WH", "defaultCultivar": "IB0488", "yieldProduct": "grain", "status": "supported", "plantingMethod": "S", "plantingDistribution": "R", "pop": 162, "row": 16, "plantDepth": 5.5, "plantWeight": -99, "sprl": 0, "symbi": "N", "photo": "C"},
    "potato": {"model": "PTSUB048", "directory": "Potato", "fileExt": "PTX", "cropCode": "PT", "defaultCultivar": "IB0002", "yieldProduct": "tuber", "status": "supported", "plantingMethod": "S", "plantingDistribution": "R", "pop": 10, "row": 71, "plantDepth": 8, "plantWeight": 1500, "sprl": 2, "symbi": "N", "photo": "R", "mh": "1", "harvestMgmt": "R"},
    "sorghum": {"model": "SGCER048", "directory": "Sorghum", "fileExt": "SGX", "cropCode": "SG", "defaultCultivar": "IB0040", "yieldProduct": "grain", "status": "supported", "plantingMethod": "S", "plantingDistribution": "R", "pop": 20, "row": 75, "plantDepth": 5, "plantWeight": -99, "sprl": 0, "symbi": "N", "photo": "C", "mh": "0", "harvestMgmt": "M", "op": 0},
    "barley": {"model": "CSCER048", "directory": "Barley", "fileExt": "BAX", "cropCode": "BA", "defaultCultivar": "IB0101", "yieldProduct": "grain", "status": "supported", "plantingMethod": "S", "plantingDistribution": "R", "pop": 225, "row": 15, "plantDepth": 2, "plantWeight": -99, "sprl": 0, "symbi": "N", "photo": "C", "mh": "0", "harvestMgmt": "M"},
    "sweetcorn": {"model": "SWCER048", "directory": "SweetCorn", "fileExt": "SWX", "cropCode": "SW", "defaultCultivar": "SW0001", "yieldProduct": "ear", "status": "supported", "plantingMethod": "S", "plantingDistribution": "R", "pop": 5.5, "row": 76, "plantDepth": 2, "plantWeight": -99, "sprl": -99, "symbi": "N", "photo": "R", "mh": "1", "harvestMgmt": "R", "op": 1},
    "pearlmillet": {"model": "MLCER048", "directory": "PearlMillet", "fileExt": "MLX", "cropCode": "ML", "defaultCultivar": "IB0033", "yieldProduct": "grain", "status": "supported", "plantingMethod": "S", "plantingDistribution": "R", "pop": 15, "row": 75, "plantDepth": 5, "plantWeight": -99, "sprl": 0, "symbi": "N", "photo": "C", "mh": "0", "harvestMgmt": "M", "op": 0},
    "sugarbeet": {"model": "BSCER048", "directory": "Sugarbeet", "fileExt": "BSX", "cropCode": "BS", "defaultCultivar": "BU0003", "yieldProduct": "root", "status": "supported", "plantingMethod": "S", "plantingDistribution": "R", "pop": 10.2, "row": 50, "plantDepth": 3, "plantWeight": -99, "sprl": -99, "symbi": "N", "photo": "L", "mh": "0", "harvestMgmt": "M", "op": 1},
}

LOCATION_PRESETS = {
    "哈尔滨": {"name": "哈尔滨", "province": "黑龙江", "lat": 45.75, "lon": 126.63, "elevationM": 150},
    "长春": {"name": "长春", "province": "吉林", "lat": 43.82, "lon": 125.32, "elevationM": 238},
    "沈阳": {"name": "沈阳", "province": "辽宁", "lat": 41.80, "lon": 123.43, "elevationM": 55},
    "北京": {"name": "北京", "province": "北京", "lat": 39.90, "lon": 116.40, "elevationM": 44},
    "石家庄": {"name": "石家庄", "province": "河北", "lat": 38.04, "lon": 114.51, "elevationM": 80},
    "济南": {"name": "济南", "province": "山东", "lat": 36.65, "lon": 117.12, "elevationM": 23},
    "郑州": {"name": "郑州", "province": "河南", "lat": 34.75, "lon": 113.62, "elevationM": 110},
    "西安": {"name": "西安", "province": "陕西", "lat": 34.26, "lon": 108.94, "elevationM": 405},
    "南京": {"name": "南京", "province": "江苏", "lat": 32.06, "lon": 118.79, "elevationM": 20},
    "合肥": {"name": "合肥", "province": "安徽", "lat": 31.82, "lon": 117.23, "elevationM": 30},
    "武汉": {"name": "武汉", "province": "湖北", "lat": 30.59, "lon": 114.31, "elevationM": 23},
    "成都": {"name": "成都", "province": "四川", "lat": 30.67, "lon": 104.06, "elevationM": 500},
    "长沙": {"name": "长沙", "province": "湖南", "lat": 28.23, "lon": 112.94, "elevationM": 45},
    "南昌": {"name": "南昌", "province": "江西", "lat": 28.68, "lon": 115.86, "elevationM": 46},
    "杭州": {"name": "杭州", "province": "浙江", "lat": 30.25, "lon": 120.16, "elevationM": 19},
    "福州": {"name": "福州", "province": "福建", "lat": 26.08, "lon": 119.30, "elevationM": 84},
    "广州": {"name": "广州", "province": "广东", "lat": 23.13, "lon": 113.26, "elevationM": 21},
    "南宁": {"name": "南宁", "province": "广西", "lat": 22.82, "lon": 108.37, "elevationM": 73},
    "昆明": {"name": "昆明", "province": "云南", "lat": 25.04, "lon": 102.71, "elevationM": 1892},
    "乌鲁木齐": {"name": "乌鲁木齐", "province": "新疆", "lat": 43.82, "lon": 87.62, "elevationM": 800},
}


def slug4(text):
    s = re.sub(r"[^A-Za-z0-9]", "", str(text or ""))
    if len(s) >= 4:
        return s[:4].upper()
    # Chinese or empty names fall back to deterministic coordinate-independent code.
    return (s.upper() + "CNXX")[:4]



def ascii_text(value, fallback="CHINA"):
    text = str(value or fallback)
    cleaned = re.sub(r"[^A-Za-z0-9 .,_-]", "", text)
    return (cleaned.strip() or fallback)[:60]


def resolve_location(req):
    loc = dict(req.get("location", {}) or {})
    key = loc.get("city") or loc.get("name")
    if key in LOCATION_PRESETS:
        merged = dict(LOCATION_PRESETS[key]); merged.update({k: v for k, v in loc.items() if v not in [None, ""]}); loc = merged
    lat = float(loc.get("lat", 45.75)); lon = float(loc.get("lon", 126.63)); elev = float(loc.get("elevationM", loc.get("elev", 150)))
    name = loc.get("name") or loc.get("city") or "Custom location"
    province = loc.get("province", "China")
    code_source = loc.get("code") or loc.get("city") or loc.get("name") or "CNLC"
    code = slug4(code_source)
    if code == "CNXX":
        code = f"C{abs(int(lat*10))%10}{abs(int(lon*10))%10}N"
    loc.update({"name": name, "province": province, "lat": lat, "lon": lon, "elevationM": elev, "stationCode": code})
    return loc


def climate_defaults(lat, lon, elev):
    # Coarse synthetic China-wide climate defaults; replace with real daily weather for production use.
    tav = max(-5.0, min(26.0, 28.0 - 0.55 * abs(lat - 20.0) - 0.006 * elev))
    amp = max(7.0, min(24.0, 8.0 + 0.45 * abs(lat - 20.0)))
    summer_rain = max(2.0, min(16.0, 12.0 - 0.04 * max(0.0, lon - 115.0) + 0.18 * max(0.0, 35.0 - lat)))
    winter_rain = 1.0 if lat > 35 else 3.0
    return tav, amp, summer_rain, winter_rain



def yday(date_text):
    dt = datetime.strptime(date_text, "%Y-%m-%d")
    return dt.year, int(dt.strftime("%j")), dt

def dssat_date(year, doy):
    return (year % 100) * 1000 + doy

def write_weather(path, year, lat, lon, elev, station_code="CNLC", tav=5.5, amp=21.0, summer_rain=8.0, winter_rain=2.0):
    lines = [
        "*WEATHER DATA : API generated synthetic weather",
        "",
        "@ INSI      LAT     LONG  ELEV   TAV   AMP REFHT WNDHT",
        f"  {station_code[:4]:<4} {lat:8.3f} {lon:8.3f} {elev:5.0f} {tav:5.1f} {amp:5.1f}   2.0   3.0",
        "@DATE  SRAD  TMAX  TMIN  RAIN  DEWP  WIND",
    ]
    for d in range(1, 366):
        mean = tav + amp * math.sin(2 * math.pi * (d - 110) / 365.0)
        rng = 11.0 + 3.0 * math.sin(2 * math.pi * (d - 100) / 365.0)
        tmax, tmin = mean + rng / 2, mean - rng / 2
        srad = max(3.5, 14.0 + 7.0 * math.sin(2 * math.pi * (d - 80) / 365.0))
        rain = 0.0
        if 105 <= d <= 285:
            if d % 5 == 0: rain += summer_rain
            if d % 13 == 0: rain += summer_rain * 2.0
            if d % 29 == 0: rain += summer_rain * 2.5
        elif d % 17 == 0:
            rain = winter_rain
        lines.append(f"{dssat_date(year,d):5d} {srad:5.1f} {tmax:5.1f} {tmin:5.1f} {rain:5.1f} -99   -99")
    with open(path, "w", encoding="ascii") as f:
        f.write("\n".join(lines) + "\n")


def write_xfile(path, req, cfg, pdate, sdate, hlast, loc, exp_code):
    mgmt = req.get("management", {}); crop = req.get("crop", {})
    lat, lon = loc["lat"], loc["lon"]; elev = loc["elevationM"]
    station = loc["stationCode"]
    fert = mgmt.get("fertilizer", {})
    n = fert.get("nitrogenKgHa", 150); p = fert.get("phosphorusKgHa", 60); k = fert.get("potassiumKgHa", 60)
    pop = mgmt.get("plantDensityPlantsHa", cfg["pop"] * 10000) / 10000.0
    row = mgmt.get("rowSpacingCm", cfg["row"]); cultivar = crop.get("cultivarCode", cfg["defaultCultivar"])
    cc = cfg["cropCode"]; model = cfg["model"]; basal_n = min(80, n); top_n = max(0, n - basal_n)
    irrig_mgmt = "R" if cc == "RI" else "N"
    fert_mgmt = "R"; harvest_mgmt = cfg.get("harvestMgmt", "M")
    mh = cfg.get("mh", "0")
    page = cfg.get("page", -99); penv = cfg.get("penv", -99); plph = cfg.get("plph", -99)
    irr_events = ""
    if cc == "RI":
        irr_events = "@I IDATE  IROP IRVAL\n" + "".join([f" 1 {pdate+i*7} IR003   100\n" for i in range(0, 8)])
    with open(path, "w", encoding="ascii") as f:
        f.write(f"""*EXP.DETAILS: {exp_code}{cc} API DEFAULT {cc} SCENARIO

*GENERAL
@PEOPLE
 API GENERATED
@ADDRESS
 {ascii_text(loc.get('province','China'))}, CHINA
@SITE
 {ascii_text(loc.get('name','China default field'), 'China default field')}

*TREATMENTS                        -------------FACTOR LEVELS------------
@N R O C TNAME.................... CU FL SA IC MP MI MF MR MC MT ME MH SM
 1 1 0 0 API {cc} DEFAULT             1  1  0  1  1  1  1  0  0  0  0  {mh}  1

*CULTIVARS
@C CR INGENO CNAME
 1 {cc} {cultivar} DEFAULT

*FIELDS
@L ID_FIELD WSTA....  FLSA  FLOB  FLDT  FLDD  FLDS  FLST SLTX  SLDP  ID_SOIL    FLNAME
 1 {station}0001 {station:<8}   -99     0 DR000     0     0 00000 -99    150  GS20200001 API field
@L ...........XCRD ...........YCRD .....ELEV .............AREA .SLEN .FLWR .SLAS FLHST FHDUR
 1 {lon:15.3f} {lat:14.3f} {elev:9.0f}                 0     0     0     0   -99   -99

*INITIAL CONDITIONS
@C   PCR ICDAT  ICRT  ICND  ICRN  ICRE  ICWD ICRES ICREN ICREP ICRIP ICRID ICNAME
 1    {cc} {sdate}   100     0     1     1   -99  1500    .8     0   100    15 -99
@C  ICBL  SH2O  SNH4  SNO3
 1    15  .300   1.0   3.0
 1    30  .300   1.0   3.0
 1    60  .280   0.8   2.0
 1    90  .260   0.8   2.0
 1   120  .230   0.5   1.5
 1   150  .220   0.5   1.5

*PLANTING DETAILS
@P PDATE EDATE  PPOP  PPOE  PLME  PLDS  PLRS  PLRD  PLDP  PLWT  PAGE  PENV  PLPH  SPRL                        PLNAME
 1 {pdate}   -99 {pop:5.1f} {pop:5.1f}     {cfg['plantingMethod']}     {cfg['plantingDistribution']} {row:5.0f}     0 {cfg['plantDepth']:5.1f} {cfg['plantWeight']:5.0f} {page:5.0f} {penv:5.0f} {plph:5.0f} {cfg['sprl']:5.0f}                        -99

*IRRIGATION AND WATER MANAGEMENT
@I  EFIR  IDEP  ITHR  IEPT  IOFF  IAME  IAMT IRNAME
 1     1    30    50   100 GS000 IR001    10 -99
{irr_events}
*FERTILIZERS (INORGANIC)
@F FDATE  FMCD  FACD  FDEP  FAMN  FAMP  FAMK  FAMC  FAMO  FOCD FERNAME
 1 {pdate} FE001 AP001    10 {basal_n:5.0f} {p:5.0f} {k:5.0f}     0     0   -99 Basal NPK
 1 {pdate+30} FE001 AP001    10 {top_n:5.0f}     0     0     0     0   -99 Topdress N

*RESIDUES AND ORGANIC FERTILIZER
@R RDATE  RCOD  RAMT  RESN  RESP  RESK  RINP  RDEP  RMET RENAME
 1 {sdate} RE001   -99   -99   -99   -99   -99   -99   -99 -99

*HARVEST DETAILS
@H HDATE  HSTG  HCOM HSIZE   HPC  HBPC HNAME
 1 {hlast} GS000     C     A   100   100 Harvest

*SIMULATION CONTROLS
@N GENERAL     NYERS NREPS START SDATE RSEED SNAME.................... SMODEL
 1 GE              1     1     S {sdate}  2150 API {cc} SCENARIO       {model}
@N OPTIONS     WATER NITRO SYMBI PHOSP POTAS DISES  CHEM  TILL   CO2
 1 OP              Y     Y     {cfg['symbi']}     N     N     N     N     Y     M
@N METHODS     WTHER INCON LIGHT EVAPO INFIL PHOTO HYDRO NSWIT MESOM MESEV MESOL
 1 ME              M     M     E     R     S     {cfg['photo']}     R     1     G     R     2
@N MANAGEMENT  PLANT IRRIG FERTI RESID HARVS
 1 MA              R     {irrig_mgmt}     {fert_mgmt}     N     {harvest_mgmt}
@N OUTPUTS     FNAME OVVEW SUMRY FROPT GROUT CAOUT WAOUT NIOUT MIOUT DIOUT VBOSE CHOUT OPOUT FMOPT
 1 OU              N     Y     Y     1     Y     N     Y     Y     N     N     Y     N     Y     A
@  AUTOMATIC MANAGEMENT
@N PLANTING    PFRST PLAST PH2OL PH2OU PH2OD PSTMX PSTMN
 1 PL          {max(1,pdate-5)} {min(99365,pdate+10)}    40   100    30    40    10
@N IRRIGATION  IMDEP ITHRL ITHRU IROFF IMETH IRAMT IREFF
 1 IR             30    50   100 GS000 IR001    10     1
@N NITROGEN    NMDEP NMTHR NAMNT NCODE NAOFF
 1 NI             30    50    25 FE001 GS000
@N RESIDUES    RIPCN RTIME RIDEP
 1 RE            100     1    20
@N HARVEST     HFRST HLAST HPCNP HPCNR
 1 HA              0 {hlast}   100     0
""")


def parse_stdout(text):
    m = re.search(r"^\s*(\d+)\s+([A-Z]{2})\s+(\d+)\s+(-?\d+)\s+(-?\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)", text, re.M)
    if not m: return {}
    g = m.groups(); v = list(map(int, [g[0], g[2], g[3], g[4], g[5], g[6], g[7], g[8], g[9], g[10], g[11]]))
    return dict(run=v[0], cropCode=g[1], treatment=v[1], anthesisDays=v[2], maturityDays=v[3], biomassKgHa=v[4], yieldKgHa=v[5], rainMm=v[6], irrigationMm=v[7], evapotranspirationMm=v[8], soilWaterMm=v[9], nitrogenUptakeKgHa=v[10], yieldKgMu=round(v[5]/15,1))


def simulate(req):
    crop_type = req.get("crop", {}).get("type", "maize").lower()
    if crop_type not in CROPS:
        return {"status":"error","error":"unsupported crop","cropType":crop_type,"supportedCrops":CROPS}
    if CROPS[crop_type]["status"] != "supported":
        return {"status":"error","error":"crop not implemented yet","cropType":crop_type,"supportedCrops":CROPS}
    cfg = CROPS[crop_type]
    loc = resolve_location(req)
    year, doy, _ = yday(req.get("plantingDate", "2026-05-15"))
    pdate = dssat_date(year, doy); sdate = dssat_date(year, max(1, doy-1)); hlast = dssat_date(year, min(365, doy+180))
    run_id = "run_" + time.strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:8]
    run_dir = os.path.join(RUNS, run_id); os.makedirs(run_dir, exist_ok=True)
    exp_code = f"{loc['stationCode']}{year%100:02d}01"
    xfile = f"{exp_code}.{cfg['fileExt']}"
    xpath = os.path.join(ROOT, cfg["directory"], xfile)
    weather_file = os.path.join(ROOT, "Weather", f"{loc['stationCode']}{year%100:02d}01.WTH")
    tav, amp, summer_rain, winter_rain = climate_defaults(loc["lat"], loc["lon"], loc["elevationM"])
    with LOCK:
        write_weather(weather_file, year, loc["lat"], loc["lon"], loc["elevationM"], loc["stationCode"], tav, amp, summer_rain, winter_rain)
        write_xfile(xpath, req, cfg, pdate, sdate, hlast, loc, exp_code)
        with open(os.path.join(ROOT,"HLJBatch.v48"),"w",encoding="ascii") as f:
            header = "@FILEX                                                                                        TRTNO     RP     SQ     OP     CO"
            line = f"{xpath:<92}{1:6d}{1:7d}{0:7d}{cfg.get('op', 0):7d}{0:7d}"
            f.write(f"$BATCH(API_{crop_type.upper()})\n!\n{header}\n{line}\n")
        cp = subprocess.run([EXE,cfg["model"],"B","HLJBatch.v48","DSCSM048.CTR"], cwd=ROOT, text=True, capture_output=True, timeout=180)
        for name in ["Summary.OUT","OVERVIEW.OUT","WARNING.OUT","PlantGro.OUT"]:
            p=os.path.join(ROOT,name)
            if os.path.exists(p): shutil.copy2(p, os.path.join(run_dir,name))
    result = parse_stdout(cp.stdout)
    scenario = dict(req); scenario["location"] = loc; scenario["weather"] = {"type": "synthetic", "tav": round(tav, 2), "amp": round(amp, 2), "summerRainEventMm": round(summer_rain, 2), "winterRainEventMm": round(winter_rain, 2)}
    return {"runId":run_id,"status":"success" if cp.returncode==0 else "error","returnCode":cp.returncode,"crop":{"type":crop_type,**CROPS[crop_type]},"scenario":scenario,"result":result,"files":{"runDir":run_dir,"summary":os.path.join(run_dir,"Summary.OUT"),"overview":os.path.join(run_dir,"OVERVIEW.OUT"),"warning":os.path.join(run_dir,"WARNING.OUT")},"stdout":cp.stdout[-2000:],"stderr":cp.stderr[-2000:]}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body):
        self.send_response(code); self.send_header("Content-Type","application/json; charset=utf-8"); self.end_headers(); self.wfile.write(json.dumps(body,ensure_ascii=False,indent=2).encode("utf-8"))
    def do_GET(self):
        if self.path == "/health": self._send(200,{"status":"ok","dssatRoot":ROOT})
        elif self.path == "/crops": self._send(200,{"crops":CROPS})
        elif self.path == "/locations": self._send(200,{"locations":LOCATION_PRESETS})
        else: self._send(404,{"error":"not found"})
    def do_POST(self):
        if self.path not in ["/simulate/maize-yield","/simulate/crop-yield"]: return self._send(404,{"error":"not found"})
        try:
            data=json.loads(self.rfile.read(int(self.headers.get("Content-Length","0") or 0)) or b"{}")
            self._send(200, simulate(data))
        except Exception as e:
            self._send(500,{"status":"error","error":str(e)})

if __name__ == "__main__":
    os.makedirs(RUNS, exist_ok=True)
    host = os.environ.get("HOST", "127.0.0.1")
    HTTPServer((host, int(os.environ.get("PORT","8765"))), Handler).serve_forever()
