


document.addEventListener("DOMContentLoaded", function () {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    document.getElementById("btn-vk").addEventListener("click", function () { // ивент на клик кнопки
        alert("Потерпите, сейчас будет таблица. (Начат скрапинг+теги)");
        fetch("/start_scraping/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken // это просто что бы работало
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === "ok") { // если норм соскрапилось то сообщаем и переход в updateresults
                updateResults();
                alert("Успешно собраны данные!");
            } else {
                alert("Ошибка!!");
            }
        })
        .catch(error => console.error("Ошибка:", error));
    });

});

function updateResults() {
    fetch("/get_results/")
        .then(response => response.json())
        .then(data => {
            if (data.top_tags) {
                let tagsList = document.querySelector(".ol-as.shadow.rounded");
                tagsList.innerHTML = "<h1 class='h1'>Топ-10 тегов:</h1>";
                let labels = [];
                let values = [];
                
                data.top_tags.forEach(tag => {
                    let popularityLabel = "обычный";
                    if (tag.popularity > 1.0) {
                        popularityLabel = "очень популярный";
                    } else if (tag.popularity > 0.5) {
                        popularityLabel = "популярный";
                    } else if (tag.popularity > 0.1) {
                        popularityLabel = "выше среднего";
                    }
                    tagsList.innerHTML += `<li><p class="p-mn">${tag.tag}: (${popularityLabel}), ${tag.popularity.toFixed(4)}</p></li>`;
                    labels.push(tag.tag);
                    values.push(tag.popularity);
                });

                // Обновляем график
                myChart.data.labels = labels;
                myChart.data.datasets[0].data = values;
                myChart.update();
            }

            // Обновляем топ-3 мемов
            if (data.top_memes) {
                let topMemesContainer = document.querySelector("#top-memes-container");
                topMemesContainer.innerHTML = "";
                data.top_memes.forEach(meme => {
                    topMemesContainer.innerHTML += `
                        <div class="col-md-4">
                            <div class="card shadow rounded">
                                <img src="${meme.image_urls[0]}" class="card-img-top" alt="${meme.text}">
                                <div class="card-body">
                                    <h5 class="card-title">${meme.text.substring(0, 50)}...</h5>
                                    <p class="card-text">Популярность: ${meme.popularity.toFixed(2)}</p>
                                </div>
                            </div>
                        </div>
                    `;
                });
            }
        })
        .catch(error => console.error("Ошибка:", error));
}