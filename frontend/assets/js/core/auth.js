/* Auth: gestión de sesión, guardias por rol y hub de secciones */
(function (w) {
  const Auth = {
    // TOKEN
    get token() {
      return localStorage.getItem("token");
    },
    set token(v) {
      if (v) localStorage.setItem("token", v);
      else localStorage.removeItem("token");
    },
    clear() {
      localStorage.removeItem("token");
    },

    // PERFIL ACTUAL
    async me() {
      if (!this.token) throw new Error("NO_TOKEN");
      // ajusta si tu backend usa /api/usuarios/me
      const u = await API.get("/usuarios/me");
      if (!u || !u.rol) throw new Error("BAD_ME_RESPONSE");
      return u; // { id, nombre, rol }
    },

    // REDIRECCIÓN POR ROL
    goToRole(rol) {
      const map = { admin: "#admin", supervisor: "#supervisor", vendedor: "#vendedor" };
      const hash = map[rol] || "";
      window.location.href = "main.html" + hash;
    },

    // GUARDIA PARA PÁGINAS O HUB
    async requireRole(expected) {
      try {
        const u = await this.me();
        const ok = Array.isArray(expected) ? expected.includes(u.rol) : u.rol === expected;
        if (!ok) {
          alert("No tienes permiso para esta vista.");
          this.goToRole(u.rol);
          return false;
        }
        const el = document.getElementById("userName");
        if (el) el.textContent = `${u.nombre ?? ""} (${u.rol})`;
        return true;
      } catch (err) {
        console.error(err);
        this.clear();
        window.location.href = "index.html";
        return false;
      }
    },

    // MONTA EL HUB: muestra solo la sección del rol (section[data-role="..."])
    async mountHub() {
      const ok = await this.requireRole(["admin", "supervisor", "vendedor"]);
      if (!ok) return null;

      const u = await this.me();

      document.querySelectorAll('section[data-role]').forEach((sec) => {
        sec.style.display = sec.dataset.role === u.rol ? "" : "none";
      });

      const btn = document.getElementById("logout");
      if (btn) btn.addEventListener("click", (e) => {
        e.preventDefault();
        this.clear();
        window.location.href = "index.html";
      });

      const want = (window.location.hash || "").slice(1);
      if (["admin", "supervisor", "vendedor"].includes(want) && want !== u.rol) {
        alert("No tienes permiso para esa vista.");
        this.goToRole(u.rol);
      }

      return u;
    },
  };

  w.Auth = Auth; // exporta a global
})(window);
