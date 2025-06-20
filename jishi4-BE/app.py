import json

from robyn import Robyn, ALLOW_CORS, jsonify

from models import session, Area

app = Robyn(__file__)
# 生产环境需要注释：使用nginx解决跨域
ALLOW_CORS(app, origins=["*"])


@app.get("/")
async def index():
    return "Welcome to Jishi"


@app.get("/getAllAreas")
async def getAllAreas():
    areas = session.query(Area).all()
    areas = [area.to_json() for area in areas]
    return jsonify({
        "status": 200,
        "message": "success",
        "areas": areas
    })


@app.post("/addNewArea")
async def addNewArea(request):
    data = request.json()
    strFields = ["name", "svgPath", "color", "hoverColor", "info"]
    arrFields = ["coordinates", "teachers"]
    dic1 = {field: data.get(field) for field in strFields}
    dic2 = {field: json.loads(data.get(field)) for field in arrFields}
    dic = {**dic1, **dic2}
    newArea = Area(**dic)
    session.add(newArea)
    session.commit()
    return jsonify({
        "status": 200,
        "message": "success",
    })


@app.post("/deleteArea")
async def deleteArea(request):
    data = request.json()
    id = data.get("id")
    area = session.query(Area).get(id)
    session.delete(area)
    session.commit()
    return jsonify({
        "status": 200,
        "message": "success",
    })


if __name__ == "__main__":
    app.start(host="0.0.0.0", port=6051)
