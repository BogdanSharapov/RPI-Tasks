import webbrowser
import argparse
import requests
import time
import plotly
from datetime import datetime
import numpy as np
from igraph import Graph, plot


def get_access_token(client_id, scope):
    assert isinstance(client_id, int), 'clinet_id must be positive integer'
    assert isinstance(scope, str), 'scope must be string'
    assert client_id > 0, 'clinet_id must be positive integer'
    url = """\
    https://oauth.vk.com/authorize?client_id={client_id}&\
    redirect_uri=https://oauth.vk.com/blank.hmtl&\
    scope={scope}&\
    &response_type=token&\
    display=page\
    """.replace(" ", "").format(client_id=client_id, scope=scope)
    webbrowser.open_new_tab(url)
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("client_id", help="Application Id", type=int)
    parser.add_argument("-s",
                        dest="scope",
                        help="Permissions bit mask",
                        type=str,
                        default="",
                        required=False)

    args = parser.parse_args()
    get_access_token(args.client_id, args.scope)

"""Task1"""
def get(url, params={}, timeout=5, max_retries=5, backoff_factor=0.3):
    """ Выполнить GET-запрос """
    attempts = 0
    while attempts < max_retries:
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()  # Вызывает исключение для статусов ошибок
            return response
        except requests.exceptions.ReadTimeout:
            time.sleep(backoff_factor * (2 ** attempts))  # Экспоненциальная задержка
            attempts += 1
        except requests.exceptions.RequestException as e:
            raise e  # Пробрасываем другие исключения
    raise requests.exceptions.RequestException("Max retries exceeded")


def get_friends(user_id, access_token, fields='bdate'):
    """ Возвращает список друзей указанного пользователя """
    assert isinstance(user_id, int), "user_id must be positive integer"
    assert user_id > 0, "user_id must be positive integer"

    domain = "https://api.vk.com/method"
    query_params = {
        'domain': domain,
        'access_token': access_token,
        'user_id': user_id,
        'fields': fields
    }

    query = "{domain}/friends.get?access_token={access_token}&user_id={user_id}&fields={fields}&v=5.53".format(
        **query_params
    )

    response = get(query)
    friends_data = response.json()

    if 'response' in friends_data:
        return friends_data['response']['items']
    else:
        return []


def age_predict(user_id, access_token):
    """ Наивное прогнозирование возраста пользователя """
    assert isinstance(user_id, int), "user_id must be positive integer"
    assert user_id > 0, "user_id must be positive integer"

    friends = get_friends(user_id, access_token)
    ages = []

    for friend in friends:
        try:
            if 'bdate' in friend:
                bdate = friend['bdate'].split('.')
                if len(bdate) == 3:  # Год рождения указан
                    year = int(bdate[2])
                    ages.append(2023 - year)  # Рассчитываем возраст
        except Exception:
            pass  # Игнорируем ошибки и продолжаем

    if ages:
        average_age = sum(ages) / len(ages)
        return average_age
    else:
        return None


"""Task 2"""


def messages_get_history(user_id, offset=0, count=200, access_token=None):
    """ Получить историю переписки с указанным пользователем """
    assert isinstance(user_id, int), "user_id must be positive integer"
    assert user_id > 0, "user_id must be positive integer"
    assert isinstance(offset, int), "offset must be positive integer"
    assert offset >= 0, "offset must be positive integer"
    assert count >= 0 and count <= 200, "count must be in the range [0, 200]"

    domain = "https://api.vk.com/method"
    query_params = {
        'domain': domain,
        'access_token': access_token,
        'user_id': user_id,
        'offset': offset,
        'count': count
    }

    query = "{domain}/messages.getHistory?access_token={access_token}&user_id={user_id}&offset={offset}&count={count}&v=5.53".format(
        **query_params
    )

    response = get(query)
    return response.json()


def count_dates_from_messages(messages):
    """ Возвращает список дат и соответствующую частоту сообщений """
    date_counts = {}

    for message in messages:
        message_date = datetime.fromtimestamp(message['date']).strftime("%Y-%m-%d")
        if message_date in date_counts:
            date_counts[message_date] += 1
        else:
            date_counts[message_date] = 1

    dates = list(date_counts.keys())
    counts = list(date_counts.values())

    return dates, counts


def plot_message_frequency(dates, counts):
    """ Строит график частоты сообщений по датам """
    plotly.tools.set_credentials_file(username='YOUR_USER_NAME', api_key='YOUR_API_KEY')
    import plotly.plotly as py
    import plotly.graph_objs as go

    x = [datetime.strptime(date, "%Y-%m-%d") for date in dates]
    data = [go.Scatter(x=x, y=counts)]
    py.iplot(data)


# Пример использования
user_id =  # PUT USER ID HERE
access_token =  # PUT ACCESS TOKEN HERE

# Получаем сообщения
history = messages_get_history(user_id)
messages = history['response']['items']

# Получаем даты и частоту сообщений
dates, counts = count_dates_from_messages(messages)

# Строим график частоты сообщений
plot_message_frequency(dates, counts)

"""Task 3"""


def get_friends(user_id, access_token):
    # функция, которая получает друзей пользователя (уже рассмотрена)
    pass  # Здесь должна быть ваша реализация функции


def get_network(users_ids, access_token, as_edgelist=True):
    """ Построение графа друзей для указанного списка пользователей """
    edges = []
    vertices = list(users_ids)

    # Получаем друзей для каждого пользователя и строим рёбра
    for user_id in users_ids:
        friends = get_friends(user_id, access_token)
        for friend in friends:
            if friend['id'] in users_ids and (friend['id'], user_id) not in edges:
                edges.append((user_id, friend['id']))

    # Создание графа
    g = Graph(vertex_attrs={"label": vertices}, edges=edges, directed=False)

    # Выделение сообществ
    communities = g.community_edge_betweenness(directed=False)
    clusters = communities.as_clustering()

    # Визуализация графа
    visual_style = {}
    visual_style["layout"] = g.layout_fruchterman_reingold(
        maxiter=1000,
        area=len(vertices) ** 3,
        repulserad=len(vertices) ** 3
    )

    pal = g.drawing.colors.ClusterColoringPalette(len(clusters))
    g.vs['color'] = pal.get_many(clusters.membership)

    plot(g, **visual_style)

    # Вернуть данные в виде списка рёбер или матрицы смежности
    if as_edgelist:
        return edges
    else:
        return g.get_adjacency().tolist()


# Пример использования
user_ids = [1234567, 7654321]  # Замените на нужные ID пользователей
access_token =  #ACCESS TOKEN HERE
network_edges = get_network(user_ids, access_token, as_edgelist=True)