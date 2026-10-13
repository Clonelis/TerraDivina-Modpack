(function () {
  "use strict";

  var repository = "Clonelis/TerraDivina-Modpack";
  var archiveName = "TerraDivina-Modpack.zip";
  var releaseTag = "modpack-download";
  var download = document.getElementById("download-link");
  var status = document.getElementById("download-status");

  function showArchiveInformation() {
    fetch("https://api.github.com/repos/" + repository + "/releases/tags/" + releaseTag, {
      headers: { Accept: "application/vnd.github+json" },
      cache: "no-store"
    }).then(function (response) {
      if (!response.ok) {
        if (response.status === 404) {
          status.textContent = "Архив ещё готовится. Попробуй зайти чуть позже.";
          download.setAttribute("aria-disabled", "true");
          download.addEventListener("click", function (event) { event.preventDefault(); });
          return null;
        }
        throw new Error("GitHub API: " + response.status);
      }
      return response.json();
    }).then(function (release) {
      if (!release) return;
      var asset = (release.assets || []).find(function (item) { return item.name === archiveName; });
      if (!asset) {
        status.textContent = "Архив временно обновляется. Попробуй чуть позже.";
        return;
      }

      download.href = asset.browser_download_url;
      var megabytes = (asset.size / 1024 / 1024).toLocaleString("ru-RU", { maximumFractionDigits: 1 });
      var updated = new Date(asset.updated_at || asset.created_at);
      var dateText = Number.isNaN(updated.getTime())
        ? ""
        : " · Обновлено " + new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "long", year: "numeric" }).format(updated);
      status.textContent = "Размер: " + megabytes + " МБ" + dateText;
    }).catch(function () {
      status.textContent = "Актуальный ZIP доступен по кнопке выше.";
    });
  }

  function showMinecraftVersions() {
    fetch("https://raw.githubusercontent.com/" + repository + "/main/manifest.json", { cache: "no-store" })
      .then(function (response) {
        if (!response.ok) throw new Error("Manifest unavailable");
        return response.json();
      })
      .then(function (manifest) {
        if (manifest.pack && manifest.pack.minecraft) {
          document.getElementById("minecraft-version").textContent = "Minecraft " + manifest.pack.minecraft;
        }
        if (manifest.menu && manifest.menu.neoforge) {
          document.getElementById("neoforge-version").textContent = "NeoForge " + manifest.menu.neoforge;
        }
      })
      .catch(function () {});
  }

  showArchiveInformation();
  showMinecraftVersions();
})();
