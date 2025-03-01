import pandas as pd
import requests
import matplotlib.pyplot as plt
from django.http import JsonResponse
from django.shortcuts import render
from io import BytesIO
import base64
from PIL import Image
from g4f.client import Client as G4FClient
from django.views.decorators.csrf import csrf_exempt
from sklearn.ensemble import RandomForestRegressor
import json

# access_token = 'vk1.a.hqCGcuQig30UfhitNqrUczsWrcRVjAhOojxj5gwDOj2ioIe2JT98KbS8HwrQLWs5JNa2JcsplHwpB8gfMxt8SJo9d7aKcBgLD6TuaKakMjoEq_5k__lzb5pTnuoz0O3BnLpiH9FEbwkA2gQ_rJLdrVVauiL0CPrF4kKGSBjnChHE8lIx-A1pAGNowkRNTn-p6uH_CgN3rq7xEJlaw3RTbw'
vk_redir = "http://127.0.0.1:8000/auth_callback/"
vk_secret = "QMeBIqE0DzM4ofSGOIAO"
vkapp_id = "52649878"
df = pd.read_csv("scraping_results.csv")
features = ["классические", "черный юмор", "политика", "постирония", "жиза", "шаблонные", "современные", "старые",
            "мудро"]
X = df[features]
y = df["popularity"]
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y)


@csrf_exempt
def predict_popularity(request):
    print("test kapec")
    if request.method == 'POST':
        data = json.loads(request.body)
        selected_tags = data.get('selectedTags', [])
        print("TEST JOSKY")
        # Создание словаря для новых постов
        new_post = {tag: 1 if tag in selected_tags else 0 for tag in features}
        X_new = pd.DataFrame([new_post])

        # Прогнозирование популярности
        prediction = model.predict(X_new)[0]

        return JsonResponse({"prediction": prediction})

    return JsonResponse({"error": "Invalid request"}, status=400)


# получение пабликов пользователя при входе через вк
def auth_callback(request):
    code = request.GET.get("code")
    if not code:
        return JsonResponse({"error": "Не получили код"}, status=400)
    token_url = f"https://oauth.vk.com/access_token?client_id={vkapp_id}&client_secret={vk_secret}&redirect_uri={vk_redir}&code={code}"
    response = requests.get(token_url).json()
    access_token = response.get("access_token")
    user_id = response.get("user_id")

    if not access_token:
        return JsonResponse({"error": "Failed to get access token"}, status=400)

    # Получаем список пабликов пользователя
    groups_url = f"https://api.vk.com/method/groups.get?user_id={user_id}&access_token={access_token}&extended=1&v=5.131"
    groups_response = requests.get(groups_url).json()

    return JsonResponse(groups_response)


# ну это просто запрос к вк апи на получение Count кол-а постов вызывается только в start_scraping
def get_vk_posts(group_id, count=25):
    url = "https://api.vk.com/method/wall.get"
    params = {"access_token": access_token, "v": "5.131", "owner_id": f"-{group_id}", "count": count}
    response = requests.get(url, params=params).json()
    return response.get("response", {}).get("items", [])



# генерит теги по каждому полученному посту
def generate_tags(image_urls, text, tags_text):
    client = G4FClient()
    tags = []
    images = []
    for image_url in image_urls:
        response = requests.get(image_url)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            images.append([image, image_url.split("/")[-1]])
    while True:
        response = client.chat.completions.create([
            {
                "content": f"Ты должен давать теги фотографиям, тебе дано N кол-во фотографий, и ты должен написать через запятую подходящие теги, ничего кроме тегов и запятой не должно быть, не надо несколько раз указывать теги, что уже были. Список тегов: {', '.join(tags_text)}. Текст поста: {text} ",
                "role": "user"}], "", images=images)
        res = response.choices[0].message.content
        print(res, image_urls)
        if len(res) > 0 and 'Model' not in res and 'error' not in res and 'chat' not in res and "discord" not in res and "exceed" not in res:
            print("Ответ GPT получен!")
            return res
            break
        return tags

import re

def gpt_tesis(text):
    client = G4FClient()
    for i in range(10):  # Пробуем максимум 10 раз
        print("Запрос к GPT ", i + 1)
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{"role": "user", "content": text}],
        )
        res = response.choices[0].message.content.strip()

        # Обрабатываем ответ GPT
        if res and 'Model' not in res and 'error' not in res and 'chat' not in res and 'date: {' not in res:
            print("Ответ GPT получен!")
            # Удаляем лишние данные (например, потоковые фрагменты)
            res = re.sub(r'data:\s*\{.*?"content":"(.*?)"\}', r'\1', res)  # Удаляем потоковые данные
            res = res.replace('data: {"content":"', '').replace('"}', '')  # Удаляем оставшиеся фрагменты
            return res.split("|")  # Разделяем ответ на отдельные пункты

    return ["Ошибка анализа от GPT"]

@csrf_exempt # фктч, включает экспериментальный режим, что бы в консоли не ругалось
def start_scraping(request):
    group_ids = [209379140, 214634115, 205549974, 169473268, 92876084, 109575676]
    if request.method == "POST":
        all_posts = []
        tag_categories = ["классические", "черный юмор", "политика", "постирония", "жиза", "шаблонные", "современные",
                          "старые", "мудро", "добрые"]
        for group_id in group_ids: # сначала проходимя по каждому паблику (его айди)
            posts = get_vk_posts(group_id) # запрашиваем у апи посты по айди
            for post in posts:
                text = post.get("text", "")
                likes = post.get("likes", {}).get("count", 0)
                reposts = post.get("reposts", {}).get("count", 0)
                views = post.get("views", {}).get("count", 0)
                images = [att["photo"]["sizes"][-1]["url"] for att in post.get("attachments", []) if
                          att["type"] == "photo"]
                if images or text: # просто проверка на наличие текста/пикчи что бы ошибок разных не было
                    tags = generate_tags(images, text, tag_categories)
                else:
                    break
                popularity = (likes * 2 + reposts * 3) / (views + 1) # моя формула расчёта популярности
                # создаём столбы с тегами (1, если тег есть, иначе 0)
                tag_dict = {tag: 1 if tag in tags else 0 for tag in tag_categories}
                all_posts.append({
                    "group_id": group_id,
                    "post_id": post["id"],
                    "text": text,
                    "image_urls": images,
                    "likes": likes,
                    "reposts": reposts,
                    "popularity": popularity,
                    **tag_dict, # модное решение капец. ** - разворачивают список
                })

        df = pd.DataFrame(all_posts)
        df.to_csv("scraping_results.csv", index=False) # по окончанию скрапинга и определения тегов сохраняем всё в csv
        print("good") # вообще можно и в эксель но как-то без разницы
        return JsonResponse({"status": "ok"}) # возвращаем js ok что бы перешёл в get_results
    print("error")
    return JsonResponse({"status": "error"}, status=400)



def get_results(request):
    df = pd.read_csv("scraping_results.csv")
    tags = ["классические", "черный юмор", "политика", "постирония", "жиза", "шаблонные", "современные",
                   "старые", "мудро", "добрые"]

    tag_stats = df[tags].multiply(df["popularity"], axis="index").mean().sort_values(ascending=False).head(10)
    top_tags = [{"tag": tag, "popularity": value} for tag, value in tag_stats.items()]
    return JsonResponse({"top_tags": top_tags})


# Create your views here.
def index(request):
    return render(request, 'index.html')

def own_test(request):
    return render(request, 'OwnTest.html')

def Analysis(request):
    df = pd.read_csv("scraping_results.csv")
    tags = [
        "классические", "черный юмор", "политика",
        "постирония", "жиза", "шаблонные",
        "современные", "старые", "мудро", "добрые"
    ]
    labels = ''
    if df.empty:
        labels = ["Дата", "Фрейм", "Абсолютно", "Пустой"]
        data = [10, 2, 4, 7]
    else:
        tag_stats = df[tags].multiply(df["popularity"], axis="index").sum() / df[tags].sum()
        tag_stats = tag_stats.sort_values(ascending=False).head(10)
        tag_stats = tag_stats.fillna(0)
        labels = list(tag_stats.index)
        data = list(map(float, tag_stats.values))

    # Получаем 3 самых популярных мема и заменяем NaN в тексте
    top_memes = []
    for _, row in df.sort_values(by="popularity", ascending=False).head(3).iterrows():
        print(row["image_urls"])
        top_memes.append({
            "image_url": json.loads(row["image_urls"].replace("'", '"')) if isinstance(row["image_urls"], str) and row["image_urls"] else None,
            "popularity": row["popularity"],
            "text": row["text"] if isinstance(row["text"], str) and row["text"] else "Без текста"
        })
    print(type(top_memes[0]["image_url"]))

    def get_popularity_label(value):
        if value > 1.0:
            return "очень популярный"
        elif value > 0.5:
            return "популярный"
        elif value > 0.1:
            return "выше среднего"
        else:
            return "обычный"

    tablo = {label: (value, get_popularity_label(value)) for label, value in zip(labels, data)}
    gpt_reaction = gpt_tesis(
        "Ты анализируешь мемы и их популярность. "
        "Тебе дана таблица тегов с их популярностью. "
        "Популярность оценивается так: "
        "больше 1.0 — очень популярный, больше 0.5 — популярный, больше 0.1 — выше среднего. "
        "Твоя задача — дать аналитический вывод. "
        "Опиши, какие тренды видны, какие темы чаще становятся популярными, а какие теряют популярность. "
        "Каждый вывод разделяй символом '|'. Нумеровать выводы не надо. Не пиши что-то по типу 'Анализируя популярность тегов мемов, можно выделить следующие тренды и темы: ', пиши сразу вывод"
        f"Таблица: {tablo}"
    )

    gpt_tendentions = gpt_tesis(
        "Ты анализируешь мемы и их популярность. "
        "Тебе дана таблица тегов с их популярностью. "
        "Популярность оценивается так: "
        "больше 1.0 — очень популярный, больше 0.5 — популярный, больше 0.1 — выше среднего. "
        "Твоя задача — дать аналитику по тенденциям мемов, какие могут стать популярными или наоборот уменьшиться в популярности. "
        "Опиши, какие тренды увядают, а какие темы становятся популярными. "
        "Каждый вывод разделяй символом '|'. Нумеровать выводы не надо. Не пиши что-то по типу 'Анализируя популярность тегов мемов, можно выделить следующие тренды и темы: ', пиши сразу вывод"
        f"Таблица: {tablo}"
    )

    return render(request, 'Analysis.html', {
        "tablo": tablo,
        "labels": labels,
        "data": data,
        "reaction": gpt_reaction,  # Передаем обработанный список выводов
        "tendentions": gpt_tendentions,  # Передаем обработанный список выводов
        "top_memes": top_memes  # Передаем топ-3 мемов в шаблон
    })