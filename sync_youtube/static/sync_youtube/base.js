let liked_songs = document.getElementsByClassName("liked-song");
// const switch_song_url = document.getElementById("switch_song_url").textContent;
// const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

var msnry = new Masonry('.main-container', {
    // options...
    itemSelector: '.remote-playlist',
    columnWidth: 30,
    percentPosition: true,
});

var drake = dragula(Array.from(document.getElementsByClassName("remote-playlist")));
drake.on("dragend", () => { msnry.layout() })
drake.on("shadow", () => { msnry.layout() })
drake.on("over", () => { msnry.layout() })

contextMenus = []
Array.from(liked_songs).forEach((element) => {
    let menu = new VanillaContextMenu({
        scope: document.querySelector('[id="' + element.id + '"]'),
        menuItems: [
            {
                label: 'Voir sur Youtube',
                callback: (event) => {
                    window.open('https://www.youtube.com/watch?v=' + event.target.attributes.youtube_id.value, '_blank');
                },
            },
            'hr',
        ],
    })

    contextMenus.push(menu)
})

function addMenuItem(options) {
    contextMenus.forEach((menu) => {
        menu.options.menuItems.push(
            options
        )
    }
    )
}

function createPlaylistEl() {
    let parent = document.querySelector(".main-container");
    let childNode = document.createElement("div")
    childNode.className = "remote-playlist"
    parent.appendChild(childNode)

    msnry.appended(childNode)
    drake.containers.push(childNode)
}
