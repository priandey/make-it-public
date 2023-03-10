let liked_songs = document.getElementsByClassName("filler");
console.log(liked_songs)
const switch_song_url = document.getElementById("switch_song_url").textContent;
const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

function handleSongClick(event) {
    event.stopPropagation();
    const node = event.currentTarget
    const id = node.id;
    fetch(switch_song_url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken,
        },
        mode: "same-origin",
        body: JSON.stringify({ id: id })
    })
        .then((response) => {
            console.log(response)
            if (response.status === 200) {
                let toggled = document.getElementById(id).parentNode.classList.toggle("deactivated")
                if (toggled === true) {
                    node.firstElementChild.textContent = "Partager cette musique"
                } else {
                    node.firstElementChild.textContent = "Ne pas partager cette musique"
                }
            }
        });
}

Array.from(liked_songs).forEach((element) => {
    element.addEventListener("click", handleSongClick);
})
