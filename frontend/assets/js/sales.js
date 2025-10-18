// frontend/assets/js/sales.js (recibos: sin IVA)
import { getJSON, postJSON, patchJSON } from './core/api.js';
import { toast } from './core/ui.js';

let productos = [];

const fmtQ = n => `Q${Number(n || 0).toFixed(2)}`;

function log(...a){ console.log("[sales]", ...a); }
function showMsg(html){ const m = document.getElementById("msg"); if(m) m.innerHTML = html || ""; }

// ---------- render & cálculo ----------
function rowHtml(p){
  return `
    <tr data-id="${p.id_producto}">
      <td>${p.id_producto}</td>
      <td>${p.nombre}</td>
      <td class="text-end" data-precio="${p.precio}">${fmtQ(p.precio)}</td>
      <td class="text-end">${Number(p.stock ?? 0)}</td>
      <td style="width:120px">
        <input type="number" class="cantidad form-control text-end"
               min="0" max="${p.stock ?? 0}" value="0">
      </td>
      <td class="text-end subtotal">Q0.00</td>
      <td style="width:130px">
        <input type="number" class="form-control text-end nuevo-stock"
               min="0" placeholder="0">
      </td>
      <td class="text-end">
        <button class="btn btn-outline-primary actualizar-stock">Actualizar</button>
      </td>
    </tr>
  `;
}

function recalcularFila(tr){
  const precio = Number(tr.querySelector('[data-precio]')?.getAttribute('data-precio') || 0);
  const cant   = Number(tr.querySelector('input.cantidad')?.value || 0);
  const sub    = precio * cant;
  const cell   = tr.querySelector('.subtotal');
  if (cell) cell.textContent = fmtQ(sub);
}

function setText(id, txt){
  const el = document.getElementById(id);
  if (el) el.textContent = txt;
}

function recalcularTotal(){
  let total = 0;
  document.querySelectorAll('#tabla-productos tr').forEach(tr=>{
    const st = Number((tr.querySelector('.subtotal')?.textContent || 'Q0').replace(/[Q,]/g,''));
    total += st;
  });

  const totalEl = document.getElementById('total');
  if (totalEl){
    // Soporta "Total: Q0.00" o solo span con número.
    if (totalEl.id === 'total' && !totalEl.closest('.footer-bar')) {
      totalEl.innerText = `Total: ${fmtQ(total)}`;
    } else {
      totalEl.textContent = fmtQ(total);
    }
  }
  return total;
}

// ---------- carga & eventos ----------
async function cargarProductos(){
  const tbody = document.getElementById("tabla-productos");
  if (!tbody) return;

  try{
    log("Consultando productos /api/productos");
    productos = await getJSON('/api/productos');  // viaja X-User-Id / X-Role

    tbody.innerHTML = "";
    if (!Array.isArray(productos) || productos.length === 0){
      showMsg(`<div class="alert alert-warning">No hay productos para mostrar.</div>`);
      setText("total", fmtQ(0));
      return;
    }

    tbody.innerHTML = productos.map(rowHtml).join("");

    // cantidades → recalcular
    tbody.querySelectorAll("input.cantidad").forEach(inp=>{
      inp.addEventListener("input", e=>{
        const tr = e.currentTarget.closest("tr");
        recalcularFila(tr);
        recalcularTotal();
      });
    });

    // Actualizar stock (suma)
    tbody.querySelectorAll(".actualizar-stock").forEach(btn=>{
      btn.addEventListener("click", async e=>{
        const tr = e.currentTarget.closest("tr");
        const id = Number(tr.dataset.id);
        const input = tr.querySelector(".nuevo-stock");
        const raw = (input.value || "").trim();

        if (raw === "" || isNaN(Number(raw))){
          showMsg(`<div class="alert alert-warning">Ingresa una cantidad válida para agregar.</div>`);
          return;
        }
        const delta = Number(raw);
        if (delta < 0){
          showMsg(`<div class="alert alert-warning">La cantidad a agregar no puede ser negativa.</div>`);
          return;
        }

        try{
          const data = await patchJSON(`/api/productos/${id}/stock`, { add: delta });
          await cargarProductos(); // repintar
          showMsg(`<div class="alert alert-info">Stock actualizado. Producto #${data.id_producto} → ${data.stock}</div>`);
          input.value = "";
          recalcularTotal();
        }catch(err){
          showMsg(`<div class="alert alert-danger">Error: ${String(err)}</div>`);
        }
      });
    });

    setText("total", fmtQ(0));
    showMsg("");
  }catch(err){
    console.error("Error cargando productos:", err);
    showMsg(`
      <div class="alert alert-danger">
        No se pudieron cargar los productos.<br>
        <small>${String(err)}</small>
      </div>
    `);
  }
}

// ---------- venta ----------
async function generarVenta(){
  showMsg("");

  // Armar items
  const items = [];
  document.querySelectorAll("#tabla-productos tr").forEach(tr=>{
    const id  = Number(tr.dataset.id);
    const qty = Number(tr.querySelector("input.cantidad")?.value || 0);
    const max = Number(tr.querySelector("input.cantidad")?.getAttribute('max') || 0);
    if (qty > 0){
      if (qty > max){
        showMsg(`<div class="alert alert-warning">La cantidad de #${id} excede el stock (${max}).</div>`);
        return;
      }
      items.push({ id_producto:id, cantidad:qty });
    }
  });

  if (items.length === 0){
    showMsg(`<div class="alert alert-warning">Selecciona cantidades para al menos un producto.</div>`);
    return;
  }

  const btn = document.getElementById("btnVender");
  if (btn){ btn.disabled = true; btn.innerText = "Procesando..."; }

  try{
    const id_usuario = Number(localStorage.getItem('userId') || 0);
    if (!id_usuario) throw new Error("No hay usuario en sesión.");

    const resp = await postJSON('/api/ventas', { id_usuario, items });
    toast?.(`Venta #${resp.id_venta} registrada. Total ${fmtQ(resp.total)}`, 'success');
    showMsg(`<div class="alert alert-success">✅ Compra exitosa. Recibo #${resp.id_venta} · Total ${fmtQ(resp.total)}</div>`);

    await cargarProductos();      // refresca stock
    recalcularTotal();            // reset total a 0
  }catch(err){
    console.error("Error registrando venta:", err);
    showMsg(`<div class="alert alert-danger">Error: ${String(err)}</div>`);
  }finally{
    if (btn){ btn.disabled = false; btn.innerText = "Registrar Venta"; }
  }
}

// ---------- abrir factura.html (bonita, separada) ----------
function abrirFacturaHtml(){
  // Encabezado (usa inputs si existen; si no, valores por defecto)
  const vendedor = document.getElementById('vendedorNombre')?.value || (localStorage.getItem('userName') || 'vendedor');
  const cliente  = document.getElementById('cliNombre')?.value || 'Consumidor final';
  const tel      = document.getElementById('cliTel')?.value || '';
  const email    = document.getElementById('cliEmail')?.value || '';
  const pago     = document.getElementById('formaPago')?.value || '';
  const fecha    = new Date().toLocaleString();

  // Items seleccionados
  const items = [];
  let total = 0;
  document.querySelectorAll('#tabla-productos tr').forEach(tr=>{
    const id    = Number(tr.dataset.id);
    const desc  = tr.children[1]?.textContent || '';
    const price = Number(tr.querySelector('[data-precio]')?.getAttribute('data-precio') || 0);
    const qty   = Number(tr.querySelector('.cantidad')?.value || 0);
    const sub   = price * qty;
    if (qty > 0){ items.push({ id, desc, price, qty, sub }); total += sub; }
  });

  if (!items.length){
    showMsg('<div class="alert alert-info">Agrega productos antes de imprimir.</div>');
    return;
  }

  // Guarda en localStorage y abre la plantilla (misma origin)
  const payload = { vendedor, cliente, tel, email, pago, fecha, items, total };
  localStorage.setItem('facturaData', JSON.stringify(payload));
  window.open('./factura.html','_blank'); // relativa al vendedor.html
}

// ---------- imprimir recibo (ticket simple) ----------
function imprimirRecibo(){
  const total = (document.getElementById('total')?.textContent || 'Q0.00');
  const fecha = new Date();
  const num = Math.floor(fecha.getTime()/1000); // número simple (timestamp)
  let detalle = '';

  document.querySelectorAll('#tabla-productos tr').forEach(tr=>{
    const desc   = tr.children[1]?.textContent || '';
    const precio = tr.children[2]?.textContent || 'Q0.00';
    const qty    = tr.querySelector('.cantidad')?.value || '0';
    const sub    = tr.querySelector('.subtotal')?.textContent || 'Q0.00';
    if (Number(qty) > 0) detalle += `${qty} x ${desc}  @ ${precio}   ${sub}\n`;
  });

  const win = window.open('', '_blank');
  win.document.write(`<pre style="font:14px/1.35 monospace;white-space:pre-wrap">
              RECIBO
No: ${num}
Fecha: ${fecha.toLocaleString()}

Detalle:
${detalle || '(sin items)'}

Total del recibo: ${total}

Este documento NO es factura ni genera crédito fiscal.
</pre>`);
  win.document.close(); win.focus(); win.print(); win.close();
}

// ---------- init ----------
function bind(){
  document.getElementById("btnVender")?.addEventListener("click", generarVenta);
  document.getElementById('histRefresh')?.addEventListener('click', cargarHistorial);
  document.getElementById('histPreset')?.addEventListener('change', cargarHistorial);


  // Botón de factura bonita (separada en factura.html + factura.css + factura.js)
  document.getElementById("btnImprimirFactura")?.addEventListener("click", abrirFacturaHtml);

  // Botón de ticket simple (compatibilidad con ambos IDs)
  document.getElementById("btnImprimirRecibo")?.addEventListener("click", imprimirRecibo);
  document.getElementById("btnImprimir")?.addEventListener("click", imprimirRecibo);
}

async function init(){
  bind();
  await cargarProductos();
  recalcularTotal();
  await cargarHistorial();
}


// Fechas a zona Guatemala en pantalla
function fmtFechaGT(dtStr){
  // Normaliza: si no trae zona, trátala como UTC agregando 'Z'
  const hasTZ = /[Z+\-]\d\d:?(\d\d)?$/.test(dtStr);
  const iso = hasTZ
    ? dtStr
    : (dtStr.includes('T') ? dtStr + 'Z' : dtStr.replace(' ', 'T') + 'Z');

  const d = new Date(iso);
  return new Intl.DateTimeFormat('es-GT', {
    dateStyle: 'short',
    timeStyle: 'medium',
    hour12: true,
    timeZone: 'America/Guatemala'
  }).format(d);
}

// ---------- historial ----------
async function cargarHistorial(){
  const preset = document.getElementById('histPreset')?.value || 'hoy';
  const tbody  = document.getElementById('tabla-historial');
  if (!tbody) return;

  try{
    const rep = await getJSON(`/api/reportes/ventas?preset=${encodeURIComponent(preset)}`);

    const filas = (rep?.ventas || []).map(v => `
      <tr>
        <td>${new Date(v.fecha).toLocaleString()}</td>
        <td>${v.vendedor || ''}</td>
        <td class="text-end">${fmtQ(v.total || 0)}</td>
      </tr>
    `).join('');

    tbody.innerHTML = filas || `<tr><td colspan="3" class="text-center muted">Sin ventas en este rango.</td></tr>`;

    const res = document.getElementById('hist-resumen');
    if (res) res.textContent = `Tickets: ${rep?.totales?.tickets ?? 0} · Total: ${fmtQ(rep?.totales?.ventas ?? 0)}`;
  }catch(err){
    tbody.innerHTML = `<tr><td colspan="3" class="text-center text-danger">Error historial: ${String(err)}</td></tr>`;
  }
}


if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
