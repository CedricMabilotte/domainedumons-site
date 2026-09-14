/* Tableaux de bord — Domaine du Mons
   Sans dépendance. Rendu SVG, survol au clavier et à la souris.
   Règle de conception : une seule échelle par graphique, jamais deux axes. */

const NS = "http://www.w3.org/2000/svg";
const nf = (n, d = 1) =>
  n === null || n === undefined || Number.isNaN(n)
    ? "—"
    : new Intl.NumberFormat("fr-FR", { minimumFractionDigits: d, maximumFractionDigits: d }).format(n);
const nf0 = (n) => nf(n, 0);

function el(tag, attrs = {}, parent = null) {
  const n = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) if (v !== null && v !== undefined) n.setAttribute(k, v);
  if (parent) parent.appendChild(n);
  return n;
}

function extremes(vals) {
  const v = vals.filter((x) => typeof x === "number" && !Number.isNaN(x));
  return v.length ? [Math.min(...v), Math.max(...v)] : [0, 1];
}

/* Échelle « jolie » : bornes arrondies et pas régulier */
function echelle(min, max, cible = 4) {
  if (min === max) { min -= 1; max += 1; }
  const brut = (max - min) / cible;
  const mag = Math.pow(10, Math.floor(Math.log10(brut)));
  const pas = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((p) => p >= brut) || 10 * mag;
  const bas = Math.floor(min / pas) * pas;
  const haut = Math.ceil(max / pas) * pas;
  const ticks = [];
  for (let v = bas; v <= haut + pas / 1000; v += pas) ticks.push(Math.round(v * 1e6) / 1e6);
  return { bas, haut, ticks };
}

/* Infobulle partagée */
let bulle = null;
function montrerBulle(hote, x, y, html) {
  if (!bulle) { bulle = document.createElement("div"); bulle.className = "infobulle"; document.body.appendChild(bulle); }
  bulle.innerHTML = html;
  bulle.style.display = "block";
  const r = hote.getBoundingClientRect();
  const bx = r.left + window.scrollX + x;
  const by = r.top + window.scrollY + y;
  bulle.style.left = Math.min(bx + 12, window.scrollX + document.documentElement.clientWidth - bulle.offsetWidth - 8) + "px";
  bulle.style.top = (by - bulle.offsetHeight - 10) + "px";
}
function cacherBulle() { if (bulle) bulle.style.display = "none"; }

/* ------------------------------------------------------------------
   graphe({conteneur, points, type, titre, unite, tendance})
   points : [{cle, libelle, y, y2?}]   y2 => bande (min/max)
   type   : "ligne" | "bande" | "barres"
   ------------------------------------------------------------------ */
function graphe(opts) {
  const { conteneur, points, type = "ligne", unite = "", tendance = null, hauteur = 190, zero = false, log = false } = opts;
  if (!conteneur) return;
  conteneur.innerHTML = "";
  if (!points || !points.length) { conteneur.innerHTML = '<p class="echec">Donnée indisponible.</p>'; return; }

  const W = 640, H = hauteur, mg = { t: 12, r: 10, b: 26, l: 40 };
  const iw = W - mg.l - mg.r, ih = H - mg.t - mg.b;

  const toutesY = points.flatMap((p) => [p.y, p.y2, p.r0, p.r1]).filter((v) => typeof v === "number");
  let e, tv;
  if (log) {
    /* échelle logarithmique : nécessaire quand un étiage et une crue tiennent dans le même graphique */
    const pos = toutesY.filter((v) => v > 0);
    const plancher = pos.length ? Math.max(Math.min(...pos) / 2, 1e-6) : 1;
    tv = (v) => Math.log10(Math.max(v, plancher));
    const [, mxp] = extremes(pos.length ? pos : [1]);
    const ticks = [];
    for (let k = Math.floor(Math.log10(plancher)); k <= Math.ceil(Math.log10(mxp)); k++)
      for (const m of [1, 2, 5]) {
        const v = m * Math.pow(10, k);
        if (v >= plancher && v <= mxp * 1.6) ticks.push(v);
      }
    e = { bas: tv(plancher), haut: tv(Math.max(mxp, plancher * 10)), ticks };
  } else {
    let [mn, mx] = extremes(toutesY);
    if (type === "barres" || zero) mn = Math.min(0, mn);
    e = echelle(mn, mx);
    tv = (v) => v;
  }
  const Y = (v) => mg.t + ih - ((tv(v) - e.bas) / (e.haut - e.bas)) * ih;
  const n = points.length;
  const X = (i) => mg.l + (n === 1 ? iw / 2 : (i / (n - 1)) * iw);
  const larg = type === "barres" ? Math.max(1, (iw / n) * 0.62) : 0;
  const Xb = (i) => mg.l + ((i + 0.5) / n) * iw;

  const env = document.createElement("div");
  env.className = "enveloppe-graphe";
  conteneur.appendChild(env);
  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", preserveAspectRatio: "none" });
  env.appendChild(svg);

  /* grille + axe Y */
  for (const t of e.ticks) {
    el("line", { class: "grille-ligne", x1: mg.l, x2: W - mg.r, y1: Y(t), y2: Y(t) }, svg);
    el("text", { class: "axe-texte", x: mg.l - 6, y: Y(t) + 4, "text-anchor": "end" }, svg).textContent = nf(t, t < 1 ? 1 : 0);
  }
  if (e.bas < 0 && e.haut > 0) el("line", { class: "trace-zero", x1: mg.l, x2: W - mg.r, y1: Y(0), y2: Y(0) }, svg);

  /* axe X : premier, milieu, dernier */
  const idx = n <= 3 ? points.map((_, i) => i) : [0, Math.floor((n - 1) / 2), n - 1];
  for (const i of idx) {
    const px = type === "barres" ? Xb(i) : X(i);
    el("text", { class: "axe-texte", x: px, y: H - 8, "text-anchor": i === 0 ? "start" : i === n - 1 ? "end" : "middle" }, svg).textContent = points[i].libelle;
  }

  /* bande de référence (quantiles d'une période de comparaison), dessinée derrière */
  if (points.some((p) => typeof p.r0 === "number")) {
    const ref = points.filter((p) => typeof p.r0 === "number");
    if (ref.length > 1) {
      const iRef = points.map((p, i) => [p, i]).filter(([p]) => typeof p.r0 === "number");
      const haut = iRef.map(([p, i]) => `${X(i)},${Y(p.r1)}`);
      const bas = iRef.map(([p, i]) => `${X(i)},${Y(p.r0)}`).reverse();
      el("polygon", { class: "trace-reference", points: haut.concat(bas).join(" ") }, svg);
      if (typeof ref[0].rm === "number")
        el("polyline", { class: "trace-mediane", points: iRef.map(([p, i]) => `${X(i)},${Y(p.rm)}`).join(" ") }, svg);
    }
  }

  /* marques */
  if (type === "bande") {
    const hautPts = points.map((p, i) => `${X(i)},${Y(p.y2)}`);
    const basPts = points.map((p, i) => `${X(i)},${Y(p.y)}`).reverse();
    el("polygon", { class: "trace-bande", points: hautPts.concat(basPts).join(" ") }, svg);
    el("polyline", { class: "trace-ligne", points: hautPts.join(" ") }, svg);
    el("polyline", { class: "trace-ligne", points: points.map((p, i) => `${X(i)},${Y(p.y)}`).join(" "), opacity: 0.55 }, svg);
  } else if (type === "barres") {
    points.forEach((p, i) => {
      if (!p.y) return;                       /* une valeur nulle ne dessine pas de trait */
      const y0 = Y(Math.max(0, e.bas)), y1 = Y(p.y);
      el("rect", { class: "trace-barre", x: Xb(i) - larg / 2, y: Math.min(y0, y1), width: larg, height: Math.max(1.5, Math.abs(y1 - y0)), rx: Math.min(2, larg / 2) }, svg);
    });
  } else {
    el("polyline", { class: "trace-ligne", points: points.map((p, i) => `${X(i)},${Y(p.y)}`).join(" ") }, svg);
  }

  if (tendance) {
    el("line", { class: "trace-tendance", x1: X(0), y1: Y(tendance.y0), x2: X(n - 1), y2: Y(tendance.y1) }, svg);
  }

  /* survol */
  const curseur = el("line", { class: "curseur", y1: mg.t, y2: mg.t + ih, style: "opacity:0" }, svg);
  const pt = el("circle", { class: "point-actif", r: 4, style: "opacity:0" }, svg);
  const zone = el("rect", { x: mg.l, y: mg.t, width: iw, height: ih, fill: "transparent" }, svg);

  function viser(clientX) {
    const r = svg.getBoundingClientRect();
    const rel = ((clientX - r.left) / r.width) * W;
    let i = type === "barres"
      ? Math.round((rel - mg.l) / (iw / n) - 0.5)
      : Math.round(((rel - mg.l) / iw) * (n - 1));
    i = Math.max(0, Math.min(n - 1, i));
    const p = points[i], px = type === "barres" ? Xb(i) : X(i);
    curseur.setAttribute("x1", px); curseur.setAttribute("x2", px); curseur.style.opacity = 0.45;
    if (type !== "barres") { pt.setAttribute("cx", px); pt.setAttribute("cy", Y(p.y2 ?? p.y)); pt.style.opacity = 1; }
    let txt = p.y2 !== undefined && p.y2 !== null
      ? `${nf(p.y)} à ${nf(p.y2)} ${unite}`
      : `${nf(p.y, Number.isInteger(p.y) ? 0 : 1)} ${unite}`;
    if (typeof p.rm === "number") txt += `<br>normale : ${nf(p.rm, 0)} ${unite}`;
    montrerBulle(env, (px / W) * env.clientWidth, (Y(p.y2 ?? p.y) / H) * env.clientHeight, `<strong>${p.cle}</strong>${txt}`);
  }
  zone.addEventListener("mousemove", (ev) => viser(ev.clientX));
  zone.addEventListener("mouseleave", () => { cacherBulle(); curseur.style.opacity = 0; pt.style.opacity = 0; });
  zone.addEventListener("touchmove", (ev) => { if (ev.touches[0]) viser(ev.touches[0].clientX); }, { passive: true });
}

/* Récupération tolérante : ne casse jamais la page */
async function json(url, ms = 12000) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), ms);
  try {
    const r = await fetch(url, { signal: ctrl.signal });
    if (!r.ok) throw new Error("HTTP " + r.status);
    return await r.json();
  } finally { clearTimeout(t); }
}

function echec(id, message) {
  const n = document.getElementById(id);
  if (n) n.innerHTML = `<p class="echec">${message}</p>`;
}

function tuile(libelle, valeur, unite, detail, etat) {
  return `<div class="tuile"${etat ? ` data-etat="${etat}"` : ""}>
    <p class="libelle">${libelle}</p>
    <p class="valeur">${valeur}${unite ? ` <span class="unite">${unite}</span>` : ""}</p>
    <p class="detail">${detail || ""}</p>
  </div>`;
}
