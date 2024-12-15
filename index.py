from datetime import datetime
from flask import Flask, render_template, request, jsonify
import requests
import folium

app = Flask(__name__, template_folder='template')

# Kakao API 키 설정
API_KEY = "c9074f42d5cd25ba8b43ce7c37ff7a72"

def get_coordinates(address):
    """
    Kakao Local API를 사용해 주소를 위도와 경도로 변환
    """
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {API_KEY}"}
    params = {"query": address}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        documents = response.json().get('documents')
        if documents:
            return float(documents[0]['y']), float(documents[0]['x'])  # 위도, 경도
    return None

def get_route_info(start_coords, end_coords, departure_time):
    """
    Kakao TMS API를 사용해 경로 및 소요 시간 정보 반환
    """
    url = "https://apis-navi.kakaomobility.com/v1/directions"
    headers = {"Authorization": f"KakaoAK {API_KEY}", "Content-Type": "application/json"}
    params = {
        "origin": f"{start_coords[1]},{start_coords[0]}",  # 경도, 위도
        "destination": f"{end_coords[1]},{end_coords[0]}",  # 경도, 위도
        "priority": "RECOMMEND",
        "departure_time": departure_time.isoformat()
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        routes = response.json().get('routes')
        if routes:
            summary = routes[0]['summary']
            duration = summary['duration'] // 60  # ms → 분 변환
            print(departure_time.isoformat(), duration)
            duration_time = int(duration)
            route = routes[0]
            coordinates = []
            for section in route['sections']:
                for road in section['roads']:
                    vertexes = road['vertexes']
                    for i in range(0, len(vertexes), 2):
                        coordinates.append((vertexes[i + 1], vertexes[i]))  # (위도, 경도)
            return duration_time, coordinates
    return None, None
def create_map(start_coords, end_coords, coodinates):
    m = folium.Map(location=start_coords, zoom_start=12)
    folium.Marker(location=start_coords, popup="출발지", icon=folium.Icon(color="blue")).add_to(m)
    folium.Marker(location=end_coords, popup="도착지", icon=folium.Icon(color="red")).add_to(m)
    folium.PolyLine(locations=coodinates, color="green", weight=2.5, opacity=1).add_to(m)
    map_html = m._repr_html_()
    return map_html
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        start_address = request.form.get("start")
        end_address = request.form.get("end")
        departure_time_str = request.form.get("departure_time")

        # 출발지와 도착지의 좌표 확인
        start_coords = get_coordinates(start_address)
        end_coords = get_coordinates(end_address)

        try:
            if departure_time_str:
                departure_time = datetime.strptime(departure_time_str, "%Y-%m-%dT%H:%M")
            else:
                departure_time = datetime.now()
        except ValueError:
            departure_time = datetime.now()  # 기본값으로 현재 시간 사용

        if start_coords and end_coords:
            # 경로 정보 가져오기
            duration, coordinates = get_route_info(start_coords, end_coords, departure_time)
            if duration:
                map_html = create_map(start_coords, end_coords, coordinates)
                return render_template(
                    "index.html",
                    duration=f"{duration} 분",
                    start=start_address,
                    end=end_address,
                    departure_time=departure_time.strftime('%Y-%m-%d %H:%M:%S'),
                    map_html=map_html
                )
            else:
                error = "경로 정보를 가져올 수 없습니다."
        else:
            error = "주소 정보를 확인할 수 없습니다."

        return render_template("index.html", error=error)

    return render_template("index.html")
# @app.route('/map', methods=["GET"])
# def map():
#     start_coords = request.args.get("start_coords")
#     end_coords = request.args.get("end_coords")
#     return jsonify({
#         "start_coods": start_coords,
#         "end_coods": end_coords
#     })
if __name__ == "__main__":
    app.run(debug=True)
