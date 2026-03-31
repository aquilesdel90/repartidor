from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os
import math

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

MAPBOX_TOKEN = os.environ.get('MAPBOX_TOKEN', '')

# ── GEOCODING ──────────────────────────────────────────────────
def geocode(address, user_lat=None, user_lon=None):
    """Convierte dirección a lat/lon usando Mapbox"""
    query = f"{address}, Argentina"
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{requests.utils.quote(query)}.json"
    params = {
        'access_token': MAPBOX_TOKEN,
        'country': 'AR',
        'language': 'es',
        'limit': 1,
    }
    # Proximidad dinámica: si tenemos GPS del usuario, Mapbox prioriza resultados cercanos
    if user_lat is not None and user_lon is not None:
        params['proximity'] = f'{user_lon},{user_lat}'
    try:
        r = requests.get(url, params=params, timeout=5)
        data = r.json()
        if data.get('features'):
            lon, lat = data['features'][0]['center']
            place_name = data['features'][0].get('place_name', address)
            return {'lat': lat, 'lon': lon, 'place_name': place_name, 'ok': True}
    except Exception as e:
        print(f"Geocoding error: {e}")
    return {'ok': False, 'address': address}

# ── DISTANCE ───────────────────────────────────────────────────
def haversine(a, b):
    """Distancia en km entre dos puntos lat/lon"""
    R = 6371
    lat1, lon1 = math.radians(a['lat']), math.radians(a['lon'])
    lat2, lon2 = math.radians(b['lat']), math.radians(b['lon'])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(h))

# ── OR-TOOLS ROUTE OPTIMIZATION ────────────────────────────────
def optimize_route_ortools(points):
    """Optimización TSP con OR-Tools. Fallback a Nearest Neighbor si no está disponible."""
    try:
        from ortools.constraint_solver import routing_enums_pb2
        from ortools.constraint_solver import pywrapcp

        n = len(points)
        # Matriz de distancias (en metros enteros para OR-Tools)
        dist_matrix = []
        for i in range(n):
            row = []
            for j in range(n):
                if i == j:
                    row.append(0)
                else:
                    row.append(int(haversine(points[i], points[j]) * 1000))
            dist_matrix.append(row)

        manager = pywrapcp.RoutingIndexManager(n, 1, 0)
        routing = pywrapcp.RoutingModel(manager)

        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return dist_matrix[from_node][to_node]

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        search_params = pywrapcp.DefaultRoutingSearchParameters()
        search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        search_params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        search_params.time_limit.seconds = 10

        solution = routing.SolveWithParameters(search_params)

        if solution:
            order = []
            index = routing.Start(0)
            while not routing.IsEnd(index):
                order.append(manager.IndexToNode(index))
                index = solution.Value(routing.NextVar(index))
            return order
    except ImportError:
        pass

    # Fallback: Nearest Neighbor
    return nearest_neighbor(points)

def nearest_neighbor(points):
    """Heurística Nearest Neighbor para TSP"""
    n = len(points)
    visited = [False] * n
    order = [0]
    visited[0] = True
    for _ in range(n - 1):
        last = order[-1]
        best_dist = float('inf')
        best_idx = -1
        for j in range(n):
            if not visited[j]:
                d = haversine(points[last], points[j])
                if d < best_dist:
                    best_dist = d
                    best_idx = j
        order.append(best_idx)
        visited[best_idx] = True
    return order

# ── ROUTES ─────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/geocode-batch', methods=['POST'])
def geocode_batch():
    """Geocodifica todas las direcciones de una vez"""
    data = request.json
    addresses = data.get('addresses', [])
    user_lat = data.get('user_lat')
    user_lon = data.get('user_lon')

    results = []
    failed = []

    for i, addr in enumerate(addresses):
        result = geocode(addr, user_lat, user_lon)
        if result['ok']:
            results.append({
                'index': i,
                'original': addr,
                'place_name': result['place_name'],
                'lat': result['lat'],
                'lon': result['lon']
            })
        else:
            failed.append({'index': i, 'original': addr})

    return jsonify({
        'geocoded': results,
        'failed': failed,
        'total': len(addresses),
        'success_count': len(results)
    })

@app.route('/api/optimize', methods=['POST'])
def optimize():
    """Recibe puntos geocodificados y devuelve orden óptimo"""
    data = request.json
    points = data.get('points', [])

    if len(points) < 2:
        return jsonify({'error': 'Necesitás al menos 2 paradas'}), 400

    order = optimize_route_ortools(points)

    # Calcular distancia total
    total_km = 0
    for i in range(len(order) - 1):
        total_km += haversine(points[order[i]], points[order[i+1]])

    ordered_points = [points[i] for i in order]

    return jsonify({
        'order': order,
        'ordered_points': ordered_points,
        'total_km': round(total_km, 1),
        'estimated_minutes': round(total_km * 2.5)  # ~24km/h promedio urbano
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
