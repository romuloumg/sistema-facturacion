// Lee los datos de impresión desde localStorage y arma la vista
const fmtQ = n => `Q${Number(n || 0).toFixed(2)}`;

function render(data){
  if (!data || !Array.isArray(data.items) || data.items.length === 0){
    document.body.innerHTML = `
      <div style="max-width:720px;margin:40px auto;font:14px/1.4 system-ui,Segoe UI,Arial">
        <h2>Sin datos para imprimir</h2>
        <p>Abre este archivo desde el botón <b>Imprimir</b> en la pantalla del vendedor.</p>
      </div>`;
    return;
  }

  // Header
  document.getElementById('fc-fecha').textContent    = data.fecha || new Date().toLocaleString();
  document.getElementById('fc-vendedor').textContent = data.vendedor || 'vendedor';
  document.getElementById('fc-cliente').textContent  = data.cliente || 'Consumidor final';

  const telW   = document.getElementById('fc-tel-wrap');
  const emailW = document.getElementById('fc-email-wrap');
  const pagoW  = document.getElementById('fc-pago-wrap');

  telW.innerHTML   = data.tel   ? `&nbsp;·&nbsp;<b>Tel:</b> ${data.tel}`     : '';
  emailW.innerHTML = data.email ? `&nbsp;·&nbsp;<b>Email:</b> ${data.email}` : '';
  pagoW.innerHTML  = data.pago  ? `&nbsp;·&nbsp;<b>Pago:</b> ${data.pago}`   : '';

  // Items
  const tbody = document.getElementById('fc-items');
  tbody.innerHTML = data.items.map(it => `
    <tr>
      <td>${it.id}</td>
      <td>${it.desc}</td>
      <td class="num">${fmtQ(it.price)}</td>
      <td class="num">${it.qty}</td>
      <td class="num">${fmtQ(it.sub)}</td>
    </tr>
  `).join('');

  // Total
  document.getElementById('fc-total').textContent = fmtQ(data.total);

  // Imprimir automáticamente
  setTimeout(() => window.print(), 150);
}

function loadData(){
  try{
    const raw = localStorage.getItem('facturaData');
    const data = raw ? JSON.parse(raw) : null;
    render(data);
    // limpia para que no se quede viejo
    setTimeout(() => localStorage.removeItem('facturaData'), 2000);
  }catch(e){
    console.error(e);
    render(null);
  }
}

if (document.readyState === 'loading'){
  document.addEventListener('DOMContentLoaded', loadData);
} else {
  loadData();
}
