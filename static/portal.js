// Tokens en memoria: al recargar hay que iniciar sesión de nuevo.
const $ = id => document.getElementById(id);
let tokens = null, nextProducts = null, nextOrders = null;
function message(text) { $('message').textContent = text; }
async function api(path, options = {}, retry = true) {
  const headers = {Accept: 'application/json', ...options.headers};
  if (options.body) headers['Content-Type'] = 'application/json';
  if (tokens) headers.Authorization = `Bearer ${tokens.access}`;
  const url = new URL(path, location.origin);
  if (url.origin !== location.origin) throw new Error('Origen no permitido.');
  const response = await fetch(url, {...options, headers, credentials:'omit'});
  if (response.status === 401 && tokens && retry) {
    const renewed = await fetch('/api/v1/auth/refresh/', {method:'POST', credentials:'omit',
      headers:{'Content-Type':'application/json'}, body:JSON.stringify({refresh:tokens.refresh})});
    if (renewed.ok) {
      tokens = await renewed.json();
      if (url.pathname === '/api/v1/auth/logout/') {
        options = {...options, body:JSON.stringify({refresh:tokens.refresh})};
      }
      return api(path, options, false);
    }
    signedOut(); throw new Error('La sesión venció. Inicia sesión nuevamente.');
  }
  const body = response.status === 204 ? null : await response.json();
  if (!response.ok) throw new Error(JSON.stringify(body?.error?.details ?? body));
  return body;
}
function post(path, data) { return api(path, {method:'POST', body:JSON.stringify(data)}); }
function card(title, detail) {
  const element = document.createElement('article'); element.className = 'module-card';
  const heading = document.createElement('h3'); heading.textContent = title;
  const text = document.createElement('p'); text.textContent = detail;
  element.append(heading,text); return element;
}
function money(value) { return new Intl.NumberFormat('es-CL',{style:'currency',currency:'CLP'}).format(value); }
async function catalogue(path='/api/v1/products/') {
  const data = await api(path);
  for (const product of data.results) {
    if (!product.active) continue;
    $('products').append(card(product.name, `${product.description} · ${money(product.price)}`));
    const option = document.createElement('option'); option.value=product.id;
    option.textContent=product.name; $('product-choice').append(option);
  }
  if (!data.count) $('products').textContent='Pronto encontrarás nuestras preparaciones aquí.';
  nextProducts=data.next; $('more-products').hidden=!nextProducts;
}
async function orders(path='/api/v1/orders/') {
  if (path === '/api/v1/orders/') $('orders').replaceChildren();
  const data = await api(path);
  if (!data.count) $('orders').textContent='Todavía no tienes pedidos.';
  for (const order of data.results) {
    const element=card(order.product_name, `${order.date} · ${order.status} · ${order.quantity} unidad(es)`);
    if (order.quote) element.append(document.createTextNode(`Cotización: ${money(order.quote)} `));
    function action(label, name, body={}) {
      const button=document.createElement('button'); button.textContent=label;
      button.onclick=async()=>{button.disabled=true; try {await post(`/api/v1/orders/${order.id}/${name}/`,body); await orders(); message('Pedido actualizado.');} catch(error){message(error.message);button.disabled=false;}};
      element.append(button);
    }
    if (order.status==='cotizado') action('Aceptar cotización','confirm',{version:order.quote_version});
    if (['solicitado','cotizado','confirmado'].includes(order.status)) action('Cancelar pedido','cancel');
    $('orders').append(element);
  }
  nextOrders=data.next; $('more-orders').hidden=!nextOrders;
}
function signedOut(){ tokens=null; $('login').hidden=false; $('registration').hidden=false; $('logout').hidden=true; $('request-order').hidden=true; $('my-orders').hidden=true; $('orders').replaceChildren(); $('identity').textContent='Inicia sesión para solicitar un pedido.'; }
function form(id, handler) {
  $(id).onsubmit=async(event)=>{event.preventDefault(); const button=event.target.querySelector('button'); button.disabled=true;
    try {await handler(Object.fromEntries(new FormData(event.target)));} catch(error){message(error.message);} finally{button.disabled=false;}};
}
form('login', async data=>{
  tokens=await post('/api/v1/auth/login/',data); $('login').reset();
  $('identity').textContent=`Sesión de ${data.username}`; $('login').hidden=true; $('registration').hidden=true;
  $('logout').hidden=false; $('request-order').hidden=false; $('my-orders').hidden=false;
  message('Sesión iniciada.'); await orders();
});
form('register',async data=>{await post('/api/v1/auth/register/',data); $('register').reset(); message('Cuenta creada. Ya puedes iniciar sesión.');});
form('reserve',async data=>{data.quantity=Number(data.quantity); await post('/api/v1/orders/',data); message('Solicitud enviada.'); await orders();});
$('logout').onclick=async()=>{try {await post('/api/v1/auth/logout/',{refresh:tokens.refresh}); message('Sesión cerrada.');} catch(error){message(`La revocación no se pudo confirmar: ${error.message}`);} finally{signedOut();}};
$('refresh-orders').onclick=()=>orders().catch(error=>message(error.message));
$('more-orders').onclick=()=>orders(nextOrders).catch(error=>message(error.message));
$('more-products').onclick=()=>catalogue(nextProducts).catch(error=>message(error.message));
catalogue().catch(error=>message(error.message));
