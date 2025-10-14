<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>POS Boutique Móvil - Login</title>
    <!-- Tailwind CSS CDN para el diseño -->
    <script src="https://cdn.tailwindcss.com"></script>
    
    <!-- NUEVOS ESTILOS PARA LA IMPRESIÓN DEL TICKET -->
    <style>
        /* Oculta toda la interfaz que no debe imprimirse */
        @media print {
            /* Ocultar el contenido principal del POS */
            body > div:not(.ticket-print-area) {
                display: none !important;
            }
            
            /* Asegura que solo el área del ticket sea visible */
            .ticket-print-area {
                display: block !important;
                width: 70mm; /* Simula un ancho de impresora térmica estándar */
                min-height: auto; 
                margin: 0 auto; /* Centra horizontalmente el ticket en la hoja */
                padding: 1cm 0; /* Añade un margen superior e inferior */
                color: #000; /* Asegura el texto negro en fondo blanco */
                font-family: monospace;
                font-size: 10px;
            }
            
            /* Fuerza el fondo blanco para ahorrar tinta y parecer un ticket */
            body {
                background-color: white !important;
                color: black !important;
                margin: 0;
                padding: 0;
            }

            /* Oculta el fondo del modal de opciones */
            #post-sale-overlay {
                background-color: transparent !important;
            }
            
            /* Alinea el contenido de la tabla del ticket al centro de la hoja */
            .ticket-content-wrapper {
                margin: 0 auto;
                text-align: center;
            }
        }
    </style>
    
    <!-- [IMPORTANTE] Cargamos las librerías de Firebase con Auth -->
    <script type="module" src="https://www.gstatic.com/firebasejs/11.6.1/firebase-app.js"></script>
    <script type="module" src="https://www.gstatic.com/firebasejs/11.6.1/firebase-firestore.js"></script>
    <script type="module" src="https://www.gstatic.com/firebasejs/11.6.1/firebase-auth.js"></script>
    
    <!-- Nuestro código principal, declarado como módulo para usar 'import' -->
    <script type="module">
        // ----------------------------------------------------
        // CONFIGURACIÓN DE PRUEBA LOCAL (¡TUS CLAVES DE FIRESTORE!)
        // ----------------------------------------------------
        const CONFIG_PRUEBA_LOCAL = {
            apiKey: "AIzaSyB3nI3X1dKQc1POeiN9VF_XXM4D3f6gMws", 
            authDomain: "boutiquepos-b6c0e.firebaseapp.com",
            projectId: "boutiquepos-b6c0e",
            storageBucket: "boutiquepos-b6c0e.appspot.com",
            messagingSenderId: "59667117483",
            appId: "1:59667117483:web:27D01a58545fb2e528ceee"
        };
        // ----------------------------------------------------

        // Importamos las funciones de Firebase
        import { initializeApp } from 'https://www.gstatic.com/firebasejs/11.6.1/firebase-app.js';
        import { getFirestore, collection, onSnapshot, doc, runTransaction, updateDoc, increment, addDoc, getDoc, query, where, getDocs } from 'https://www.gstatic.com/firebasejs/11.6.1/firebase-firestore.js';
        import { getAuth, signInWithCustomToken, signInAnonymously, onAuthStateChanged } from 'https://www.gstatic.com/firebasejs/11.6.1/firebase-auth.js';
        
        // Lógica para usar la configuración local si no estamos en el entorno de Canvas
        const firebaseConfig = 
            typeof __firebase_config !== 'undefined' 
                ? JSON.parse(__firebase_config) 
                : CONFIG_PRUEBA_LOCAL;

        // Definición de variables globales
        const appId = typeof __app_id !== 'undefined' ? __app_id : firebaseConfig.projectId;

        let db;
        let auth;
        let currentUserId = 'ANÓNIMO'; // Se actualiza tras el login
        let cart = [];
        let inventory = {}; // Cache local del inventario
        
        // -----------------------------------------------------------------------
        // Inicialización y Configuración Global
        // -----------------------------------------------------------------------
        function initFirebase() {
            try {
                if (Object.keys(firebaseConfig).length > 0) {
                    const app = initializeApp(firebaseConfig);
                    db = getFirestore(app);
                    auth = getAuth(app); // Inicializar Auth
                    
                    // [CORRECCIÓN CRÍTICA] Forzar inicio de sesión anónimo si no hay usuario
                    onAuthStateChanged(auth, (user) => {
                        if (!user) {
                            signInAnonymously(auth)
                                .then(() => {
                                    console.log("Autenticación anónima forzada exitosa.");
                                })
                                .catch((error) => {
                                    console.error("Fallo la autenticación anónima:", error);
                                    showMessage("Error de Auth en Firebase. Revise reglas.", "bg-red-800");
                                });
                        }
                    });
                    
                    // Exponer funciones al alcance global para que el HTML pueda llamarlas
                    window.handleLogin = handleLogin;
                    window.handleLogout = handleLogout; // Exponer la función de Logout
                    window.handleProductInput = handleProductInput;
                    window.showItemOptions = showItemOptions;
                    window.updateItemQuantity = updateItemQuantity;
                    window.removeItem = removeItem;
                    window.openPaymentModal = openPaymentModal;
                    window.togglePaymentFields = togglePaymentFields;
                    window.calculateChange = calculateChange;
                    window.finalizeSale = finalizeSale;
                    window.closeModal = closeModal;
                    window.closePaymentModal = closePaymentModal;
                    window.printTicket = printTicket;
                    window.sendEmailTicket = sendEmailTicket; 
                    
                    // Exponer funciones de Quick Action
                    window.openInventorySearchModal = openInventorySearchModal;
                    window.searchInventory = searchInventory;
                    window.closeInventorySearchModal = closeInventorySearchModal;
                    
                } else {
                    console.warn("Firebase no inicializado: Faltan __firebase_config. La aplicación no funcionará correctamente.");
                }
            } catch (e) {
                console.error("Error al inicializar Firebase:", e);
            }
        }
        
        // --- LÓGICA DE AUTENTICACIÓN ---
        
        async function handleLogin() {
            let username = document.getElementById('username-input').value.trim();
            const password = document.getElementById('password-input').value.trim();
            
            if (!username || !password) {
                 showMessage("Ingrese usuario (E###) y contraseña.", "bg-yellow-600");
                 return;
            }
            
            showMessage("Iniciando sesión...", "bg-blue-600");
            
            try {
                // 1. Normalizar el nombre de usuario
                let userDocId = username.toUpperCase();
                
                // 2. Manejar el alias 'ADMIN' o 'admin' para E001
                if (userDocId === 'ADMIN') {
                    userDocId = 'E001';
                }

                // 3. Buscar usuario en Firestore
                const userDocRef = doc(db, 'users', userDocId);
                const userDoc = await getDoc(userDocRef);

                if (!userDoc.exists()) {
                    showMessage("Usuario no encontrado (EID incorrecto).", "bg-red-600");
                    document.getElementById('password-input').value = ''; 
                    return;
                }

                const userData = userDoc.data();

                if (userData.password !== password) {
                    showMessage("Contraseña incorrecta.", "bg-red-600");
                    document.getElementById('password-input').value = ''; 
                    return;
                }
                
                // --- LOGIN EXITOSO ---
                // Simulación del cambio de vista
                currentUserId = userDocId;
                document.getElementById('pos-screen').classList.remove('hidden');
                document.getElementById('login-screen').classList.add('hidden');
                document.getElementById('user-display').textContent = `Usuario: ${currentUserId}`;
                
                // Reset de campos de login
                document.getElementById('username-input').value = '';
                document.getElementById('password-input').value = '';

                fetchInventory(); 
                showMessage(`Bienvenido, ${userData.full_name || userDocId}.`, "bg-green-600");

            } catch (e) {
                 console.error("Error durante el login:", e);
                 // Si falla por permisos aquí, el error más probable es que no se puede leer 'users'.
                 showMessage("Error: Revise permisos de lectura para 'users'.", "bg-red-700");
            }
        }
        
        function handleLogout() {
            // Limpiar y resetear vistas
            currentUserId = 'ANÓNIMO';
            document.getElementById('pos-screen').classList.add('hidden');
            document.getElementById('login-screen').classList.remove('hidden');
            document.getElementById('user-display').textContent = `Usuario: ANÓNIMO`;
            cart = [];
            updateCartDisplay();
            showMessage("Sesión cerrada.", "bg-gray-500");
        }

        // --- Lógica del Sistema POS ---
        
        async function fetchInventory() {
            if (!db) { return; }

            try {
                // Suscripción a inventario en tiempo real
                onSnapshot(collection(db, 'inventory'), (snapshot) => {
                    inventory = {};
                    snapshot.forEach(doc => {
                        inventory[doc.id] = { ...doc.data(), id: doc.id };
                    });
                    console.log("Inventario cargado o actualizado desde Firestore.");
                    document.getElementById('product-input').placeholder = "Escanear o buscar SKU";
                    updateCartDisplay(); // Para asegurar que los precios sean correctos si hay cambios
                }, error => {
                    console.error("Error al suscribirse a inventario:", error);
                    // Esto indica un problema de REGLAS DE SEGURIDAD.
                    document.getElementById('product-input').placeholder = "ERROR: Revisar Reglas de Seguridad.";
                });

            } catch (e) {
                console.error("Error al cargar inventario:", e);
            }
        }
        
        function getProductBySKU(sku) {
            // Busca el SKU exactamente en mayúsculas
            return inventory[sku.toUpperCase()];
        }

        function calculateCartTotals() {
            let subtotal = 0;
            cart.forEach(item => {
                subtotal += item.price * item.quantity;
            });
            document.getElementById('subtotal-display').textContent = `$${subtotal.toFixed(2)}`;
            return subtotal;
        }

        function updateCartDisplay() {
            const cartList = document.getElementById('cart-list');
            const emptyMsg = document.getElementById('empty-cart-msg');
            cartList.innerHTML = '';

            if (cart.length === 0) {
                emptyMsg.classList.remove('hidden');
            } else {
                emptyMsg.classList.add('hidden');
                cart.forEach((item, index) => {
                    const totalItemPrice = item.price * item.quantity;
                    const li = document.createElement('li');
                    li.className = 'flex justify-between items-center p-3 border-b border-gray-700 hover:bg-gray-700 cursor-pointer text-sm md:text-base';
                    li.setAttribute('data-index', index);
                    
                    // [CORRECCIÓN CLAVE] Enlazar el evento onclick directamente a la función
                    li.onclick = () => showItemOptions(index); 
                    
                    li.innerHTML = `
                        <div class="flex-1">
                            <div class="font-bold text-white">${item.name}</div>
                            <div class="text-gray-400 text-xs md:text-sm">${item.sku}</div>
                        </div>
                        <div class="w-1/4 text-right text-yellow-400 font-bold">$${totalItemPrice.toFixed(2)}</div>
                        <div class="w-1/6 text-right text-white font-bold">${item.quantity}x</div>
                    `;
                    cartList.appendChild(li);
                });
            }
            
            calculateCartTotals();
        }
        
        function getPriceForQuantity(productInfo, quantity) {
            // Lógica de mayoreo simplificada (debe coincidir con la de Python)
            if (quantity >= 500 && productInfo.price_500) return productInfo.price_500;
            if (quantity >= 300 && productInfo.price_300) return productInfo.price_300;
            if (quantity >= 100 && productInfo.price_100) return productInfo.price_100;
            if (quantity >= 50 && productInfo.price_50) return productInfo.price_50;
            if (quantity >= 12 && productInfo.price_12) return productInfo.price_12;
            if (quantity >= 5 && productInfo.price_5) return productInfo.price_5;
            
            return productInfo.price;
        }

        function addProductToCart(sku) {
            const product = getProductBySKU(sku);
            if (!product) {
                showMessage("Producto no encontrado.", "bg-red-500");
                return;
            }
            
            let existingItem = cart.find(item => item.sku === sku);
            let newQuantity = existingItem ? existingItem.quantity + 1 : 1;

            if (newQuantity > product.quantity) {
                showMessage("Stock insuficiente para añadir.", "bg-yellow-500");
                return;
            }
            
            if (existingItem) {
                existingItem.quantity = newQuantity;
            } else {
                existingItem = { 
                    sku: sku, 
                    name: product.name, 
                    quantity: 1, 
                    price: product.price // Precio base inicial
                };
                cart.push(existingItem);
            }
            
            // Reaplicar lógica de mayoreo
            existingItem.price = getPriceForQuantity(product, existingItem.quantity);
            
            updateCartDisplay();
            showMessage(`Añadido: ${existingItem.name}`, "bg-green-500");
        }
        
        function handleProductInput(event) {
            if (event.key === 'Enter') {
                const input = event.target;
                const sku = input.value.trim();
                if (sku) {
                    addProductToCart(sku);
                    input.value = '';
                }
            }
        }

        // --- Modales ---

        function closeModal() {
            document.getElementById('modal-overlay').classList.add('hidden');
        }

        function closePaymentModal() {
            document.getElementById('payment-overlay').classList.add('hidden');
        }

        function closePostSaleModal() {
            document.getElementById('post-sale-overlay').classList.add('hidden');
        }

        function closeInventorySearchModal() {
            document.getElementById('inventory-search-modal-overlay').classList.add('hidden');
        }

        function openInventorySearchModal() {
            document.getElementById('inventory-search-modal-overlay').classList.remove('hidden');
            document.getElementById('inventory-search-input').focus();
        }

        function searchInventory() {
            const searchTerm = document.getElementById('inventory-search-input').value.trim().toLowerCase();
            const resultsDiv = document.getElementById('inventory-results');
            resultsDiv.innerHTML = '';
            
            if (!searchTerm) {
                resultsDiv.innerHTML = '<p class="text-gray-400">Ingrese un término para buscar.</p>';
                return;
            }

            const matches = Object.values(inventory).filter(product => 
                product.name.toLowerCase().includes(searchTerm) || product.id.toLowerCase().includes(searchTerm)
            );

            if (matches.length === 0) {
                resultsDiv.innerHTML = '<p class="text-red-400">No se encontraron productos.</p>';
                return;
            }

            let resultsHtml = `<ul class="space-y-2">`;
            matches.forEach(product => {
                resultsHtml += `
                    <li class="p-2 border-b border-gray-600 flex justify-between items-center hover:bg-gray-600 rounded">
                        <div>
                            <p class="font-bold text-white">${product.name}</p>
                            <p class="text-xs text-gray-400">SKU: ${product.id}</p>
                        </div>
                        <p class="font-bold text-yellow-400 text-right">Stock: ${product.quantity}</p>
                    </li>
                `;
            });
            resultsHtml += `</ul>`;
            resultsDiv.innerHTML = resultsHtml;
        }

        
        // --- Opciones de Ítem ---

        function showItemOptions(index) {
            const item = cart[index];
            const product = getProductBySKU(item.sku);
            
            const dialogContent = document.getElementById('modal-content');
            dialogContent.innerHTML = `
                <h3 class="text-xl font-bold mb-4 text-white">Modificar ${item.name}</h3>
                <p class="mb-4 text-gray-300">Cantidad actual: ${item.quantity} (Stock: ${product ? product.quantity : 'N/A'})</p>
                <input type="number" id="new-qty-input" value="${item.quantity}" min="1" max="${product ? product.quantity : 1}" 
                       class="w-full p-2 bg-gray-700 border border-gray-600 rounded text-white mb-4">
                
                <div class="flex justify-between space-x-2">
                    <button onclick="updateItemQuantity(${index})" class="flex-1 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg shadow-md">
                        Actualizar Cantidad
                    </button>
                    <button onclick="removeItem(${index})" class="py-2 px-4 bg-red-600 hover:bg-red-700 text-white font-bold rounded-lg shadow-md">
                        Eliminar
                    </button>
                </div>
            `;
            document.getElementById('modal-overlay').classList.remove('hidden');
        }

        function updateItemQuantity(index) {
            const newQty = parseInt(document.getElementById('new-qty-input').value);
            const item = cart[index];
            const product = getProductBySKU(item.sku);
            
            if (isNaN(newQty) || newQty <= 0) {
                 showMessage("Cantidad inválida.", "bg-red-500");
                 return;
            }
            if (product && newQty > product.quantity) {
                showMessage("Stock insuficiente.", "bg-red-500");
                return;
            }
            
            item.quantity = newQty;
            item.price = product ? getPriceForQuantity(product, newQty) : item.price;
            
            updateCartDisplay();
            closeModal();
        }

        function removeItem(index) {
            cart.splice(index, 1);
            updateCartDisplay();
            closeModal();
            showMessage("Artículo eliminado.", "bg-red-500");
        }
        
        // --- Ventana de Pago ---
        
        function openPaymentModal() {
            if (cart.length === 0) {
                showMessage("El carrito está vacío.", "bg-yellow-500");
                return;
            }
            
            const total = calculateCartTotals();
            const paymentContent = document.getElementById('payment-modal-content');
            
            paymentContent.innerHTML = `
                <h3 class="text-2xl font-bold mb-6 text-white">TOTAL: $${total.toFixed(2)}</h3>
                
                <div class="mb-4">
                    <label class="block text-gray-400 mb-1">Método de Pago</label>
                    <select id="payment-method" onchange="togglePaymentFields(this.value)" class="w-full p-3 bg-gray-700 border border-gray-600 rounded text-white">
                        <option value="Efectivo">Efectivo</option>
                        <option value="Tarjeta Bancaria">Tarjeta Bancaria</option>
                        <option value="Transferencia">Transferencia</option>
                    </select>
                </div>

                <div id="payment-fields" class="mb-4">
                    <label class="block text-gray-400 mb-1">Monto Recibido</label>
                    <input type="number" id="received-amount" oninput="calculateChange(${total})" placeholder="0.00" class="w-full p-3 bg-gray-700 border border-gray-600 rounded text-white">
                    <p class="text-lg mt-2 text-green-400">Cambio: <span id="change-display">$0.00</span></p>
                </div>

                <button onclick="finalizeSale(${total})" class="w-full py-3 bg-green-600 hover:bg-green-700 text-white font-bold rounded-lg shadow-lg">
                    Confirmar Pago
                </button>
            `;
            document.getElementById('payment-overlay').classList.remove('hidden');
        }
        
        function togglePaymentFields(method) {
             const fieldsDiv = document.getElementById('payment-fields');
             const total = calculateCartTotals();

             if (method === 'Efectivo') {
                 fieldsDiv.innerHTML = `
                    <label class="block text-gray-400 mb-1">Monto Recibido</label>
                    <input type="number" id="received-amount" oninput="calculateChange(${total})" placeholder="0.00" class="w-full p-3 bg-gray-700 border border-gray-600 rounded text-white">
                    <p class="text-lg mt-2 text-green-400">Cambio: <span id="change-display">$0.00</span></p>
                 `;
             } else {
                 fieldsDiv.innerHTML = `
                    <label class="block text-gray-400 mb-1">Folio de Transacción</label>
                    <input type="text" id="folio-input" placeholder="Folio de transacción/referencia" class="w-full p-3 bg-gray-700 border border-gray-600 rounded text-white">
                 `;
             }
        }
        
        function calculateChange(total) {
            const receivedInput = document.getElementById('received-amount');
            const changeDisplay = document.getElementById('change-display');
            try {
                const received = parseFloat(receivedInput.value);
                const change = received - total;
                changeDisplay.textContent = `$${change.toFixed(2)}`;
                if (change < 0) {
                     changeDisplay.classList.remove('text-green-400');
                     changeDisplay.classList.add('text-red-400');
                } else {
                     changeDisplay.classList.remove('text-red-400');
                     changeDisplay.classList.add('text-green-400');
                }
            } catch {
                changeDisplay.textContent = `$0.00`;
            }
        }

        // --- Finalización de Venta (Transacción Corregida) ---

        async function finalizeSale(total) {
            if (!db) {
                showMessage("ERROR: Base de datos no conectada. Venta no registrada.", "bg-red-700");
                return;
            }

            const method = document.getElementById('payment-method').value;
            // [CORRECCIÓN] Capturar el nombre del cliente aquí, antes de limpiar el campo
            const customerName = document.getElementById('customer-name').value || "Público General"; 
            let details = {};
            
            // --- Validaciones de Pago ---
            if (method === 'Efectivo') {
                const received = parseFloat(document.getElementById('received-amount').value);
                if (received < total) {
                    showMessage("Monto recibido insuficiente.", "bg-red-500");
                    return;
                }
                details = { received: received, change: received - total };
            } else {
                const folio = document.getElementById('folio-input').value.trim();
                if (!folio) {
                    showMessage("El folio de transacción es obligatorio.", "bg-yellow-500");
                    return;
                }
                details = { folio: folio };
            }

            showMessage("Venta en curso. No cierre la aplicación...", "bg-blue-600");
            
            // [CORRECCIÓN] Declarar variables en el ámbito superior (fuera del try/catch)
            let newTicketNumber = 0;
            let saleItemsData = []; 
            const stockUpdates = []; 
            
            // --- INICIO DE LA TRANSACCIÓN CRÍTICA DE FIRESTORE ---
            try {
                
                await runTransaction(db, async (transaction) => {
                    
                    // --- 1. LECTURAS (READS - TODAS SE EJECUTAN PRIMERO) ---
                    // A. Obtener la configuración actual (para el número de ticket)
                    const configRef = doc(db, 'config', 'app_config');
                    const configDoc = await transaction.get(configRef);
                    
                    // B. Obtener todos los documentos del inventario en el carrito
                    const itemRefs = cart.map(item => doc(db, 'inventory', item.sku));
                    const itemDocs = await Promise.all(itemRefs.map(ref => transaction.get(ref)));

                    // --- 2. VALIDACIONES Y PREPARACIÓN DE DATOS ---

                    // Determinar el nuevo número de ticket
                    newTicketNumber = (configDoc.data().last_ticket_number || 0) + 1;

                    // Validar stock y obtener el stock actual para cada ítem.
                    for (let i = 0; i < cart.length; i++) {
                        const item = cart[i];
                        const itemDoc = itemDocs[i];
                        
                        if (!itemDoc.exists) {
                            throw new Error(`Item ${item.sku} no encontrado en inventario.`);
                        }
                        
                        const currentQuantity = itemDoc.data().quantity;
                        const newQuantity = currentQuantity - item.quantity;
                        
                        if (newQuantity < 0) {
                            throw new Error(`Stock insuficiente para ${item.name}. Venta cancelada.`);
                        }
                        
                        saleItemsData.push({
                            sku: item.sku, name: item.name, quantity: item.quantity, price: item.price // Precio efectivo
                        });
                        
                        // Almacenar la referencia y el nuevo valor para la ESCRITURA
                        stockUpdates.push({
                            ref: itemRefs[i],
                            newQuantity: newQuantity
                        });
                    }

                    // Preparar el registro de venta
                    const saleRecord = {
                        ticket_number: newTicketNumber,
                        timestamp: new Date().toISOString(),
                        user: currentUserId, // Usar el ID del usuario autenticado
                        customer_name: customerName,
                        items: saleItemsData,
                        total: total,
                        payment_method: method,
                        payment_details: details,
                        status: "COMPLETADA"
                    };
                    
                    // --- 3. ESCRITURAS (WRITES - TODAS LAS ESCRITURAS DESPUÉS DE LAS LECTURAS) ---
                    
                    // A. Registrar la venta en la colección raíz 'sales'
                    const salesCollectionRef = collection(db, 'sales'); 
                    // Usar el número de ticket como ID del documento (esto es lo que espera el escritorio)
                    const newSaleRef = doc(salesCollectionRef, newTicketNumber.toString()); 
                    transaction.set(newSaleRef, saleRecord);
                    
                    // B. Actualizar el stock del inventario
                    stockUpdates.forEach(update => {
                         transaction.update(update.ref, { quantity: update.newQuantity });
                    });
                    
                    // C. Actualizar el contador de tickets
                    transaction.update(configRef, { last_ticket_number: newTicketNumber });

                    // La transacción se commite automáticamente si no hay errores
                });

                // --- FUERA DE LA TRANSACCIÓN (ÉXITO) ---
                
                closePaymentModal();
                const successfulSaleMsg = `Venta $${total.toFixed(2)} finalizada (Ticket #${newTicketNumber}).`;
                showMessage(successfulSaleMsg, "bg-green-600");
                
                // Limpiar después de la venta exitosa
                cart = [];
                updateCartDisplay();
                document.getElementById('customer-name').value = ''; 
                
                // [LLAMADA FINAL] showPostSaleOptions recibe el customerName capturado al inicio
                showPostSaleOptions(newTicketNumber, total, saleItemsData, customerName); // Pasar customerName

            } catch (error) {
                closePaymentModal();
                console.error("Error en la transacción:", error);
                showMessage(`ERROR: ${error.message || 'Fallo desconocido de la DB.'}`, "bg-red-700");
            }
        }

        // --- Opciones Post-Venta ---
        
        function prepareTicketContent(ticketNumber, total, saleItems, customerName) {
            // El nombre del cliente se recibe como argumento
            const customerDisplay = customerName || "Público General"; 
            
            // Función auxiliar para generar el contenido del ticket en formato simple
            let itemsText = ``;
            saleItems.forEach(item => {
                const totalItemPrice = item.price * item.quantity;
                const line = `${item.quantity}x ${item.name}`;
                const totalLine = `$${totalItemPrice.toFixed(2)}`;
                itemsText += `${line} ${totalLine}\n`; 
            });
            
            const date = new Date().toLocaleDateString('es-MX');
            const time = new Date().toLocaleTimeString('es-MX');
            
            // [MODIFICACIÓN CLAVE] Usar HTML para el centrado y el logo
            return `
<div class="ticket-content-wrapper" style="width: 100%; text-align: center;">
    <!-- [NUEVO] Insertar el logo y centrarlo -->
    <img src="logo.jpg" style="width: 50px; height: 50px; margin: 0 auto; display: block; border-radius: 5px; margin-bottom: 5px;" alt="Logo Boutique">
    
    <p style="font-weight: bold; font-size: 1.1em; margin: 5px 0;">BOUTIQUE EL IMPULSO</p>
    <p style="font-size: 0.9em; margin-bottom: 10px;">----------------------------------------</p>
    
    <div style="text-align: left; margin-bottom: 5px; width: 100%;">
        Ticket N°: ${ticketNumber}<br>
        Fecha: ${date} ${time}<br>
        Cliente: ${customerDisplay} <br> 
        Atendido por: ${currentUserId}
    </div>
    <p style="font-size: 0.9em; margin-bottom: 5px;">----------------------------------------</p>

    <!-- Sección de Ítems (usando una tabla para mejor alineación en la impresión) -->
    <table style="width: 100%; text-align: left; font-size: 1em; font-family: monospace;">
        ${saleItems.map(item => 
            `<tr>
                <td style="width: 70%; padding: 1px 0;">${item.quantity}x ${item.name.substring(0, 25)}</td>
                <td style="width: 30%; text-align: right; padding: 1px 0;">$${(item.price * item.quantity).toFixed(2)}</td>
            </tr>`).join('')}
    </table>

    <p style="font-size: 0.9em; margin-top: 5px;">----------------------------------------</p>
    
    <div style="text-align: right; font-weight: bold; font-size: 1.2em; width: 100%; padding: 5px 0;">
        TOTAL: $${total.toFixed(2)}
    </div>

    <div style="text-align: center; margin-top: 15px; font-size: 0.9em; width: 100%;">
        <p>¡Gracias por su compra!</p>
        
        <!-- Leyenda Legal y Devoluciones -->
        <p style="margin-top: 15px; font-size: 0.8em; line-height: 1.2;">
            Este ticket de compra NO ES UN<br>
            COMPROBANTE FISCAL.<br>
            Para devoluciones solamente se cuenta<br>
            con 7 días naturales a partir de la<br>
            fecha de compra.
        </p>
    </div>
</div>
`;
        }

        function printTicket(ticketNumber, total, saleItems, customerName) {
            closePostSaleModal();
            
            const ticketContent = prepareTicketContent(ticketNumber, total, saleItems, customerName);
            
            const printArea = document.getElementById('print-area');
            printArea.innerHTML = ticketContent; // Insertamos el HTML directo
            
            // Forzamos un pequeño retraso para asegurar que el DOM se actualice antes de imprimir
            setTimeout(() => {
                window.print();
                
                // Limpiar el área después de imprimir
                printArea.innerHTML = '';
            }, 100); 
        }

        function sendEmailTicket(ticketNumber) {
             const emailInput = document.getElementById('email-input-post-sale');
             const recipient = emailInput.value.trim();

             if (!recipient || !recipient.includes('@')) {
                 showMessage("Ingrese un correo válido para continuar.", "bg-red-500");
                 return;
             }
             
             // Creamos el enlace mailto: que abre la aplicación de correo del dispositivo
             const subject = encodeURIComponent(`Su Ticket de Compra - Boutique El Impulso (Ticket #${ticketNumber})`);
             const body = encodeURIComponent(`¡Hola!\n\nAdjunto encontrará el ticket de compra (debe adjuntarlo manualmente si lo guardó como PDF).\n\nGracias por su preferencia.`);

             window.location.href = `mailto:${recipient}?subject=${subject}&body=${body}`;
             
             // Muestra un mensaje al usuario después de abrir la app de correo
             showMessage("Abriendo aplicación de correo. Adjunte el PDF manualmente.", "bg-blue-600");
             closePostSaleModal();
        }


        function showPostSaleOptions(ticketNumber, total, saleItems, customerName) {
            // El customerName se pasa desde finalizeSale, por lo que este campo se limpia después.
            const optionsContent = document.getElementById('post-sale-content');
            optionsContent.innerHTML = `
                <h3 class="text-2xl font-bold mb-4 text-white">Venta #${ticketNumber} Finalizada</h3>
                <p class="mb-6 text-gray-300">Total: $${total.toFixed(2)}</p>
                
                <p class="text-sm text-yellow-400 mb-2">Para adjuntar el ticket, primero use 'Imprimir Ticket' y guárdelo como PDF.</p>

                <button onclick="printTicket(${ticketNumber}, ${total}, ${JSON.stringify(saleItems).replace(/"/g, "'")}, '${customerName}')" class="w-full py-3 mb-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg shadow-md">
                    Imprimir Ticket (Guardar PDF)
                </button>
                
                <div class="mb-4">
                     <input type="email" id="email-input-post-sale" placeholder="Correo electrónico del cliente"
                            class="w-full p-2 bg-gray-700 border border-gray-600 rounded text-white focus:ring-yellow-500 focus:border-yellow-500">
                </div>

                <button onclick="sendEmailTicket(${ticketNumber})" class="w-full py-3 mb-4 bg-green-600 hover:bg-green-700 text-white font-bold rounded-lg shadow-md">
                    Enviar Ticket por Correo
                </button>
                
                <button onclick="closePostSaleModal()" class="w-full py-3 bg-gray-500 hover:bg-gray-600 text-white font-bold rounded-lg shadow-md">
                    Listo
                </button>
            `;
            document.getElementById('post-sale-overlay').classList.remove('hidden');
        }

        function showMessage(msg, style) {
            const msgBox = document.getElementById('message-box');
            msgBox.textContent = msg;
            msgBox.className = `fixed bottom-4 left-1/2 transform -translate-x-1/2 p-3 rounded-lg text-white font-bold shadow-xl transition-opacity duration-300 ${style}`;
            msgBox.classList.remove('opacity-0');
            
            setTimeout(() => {
                msgBox.classList.add('opacity-0');
            }, 3000);
        }

        window.onload = initFirebase;

    </script>
</head>
<body class="bg-gray-900 text-white font-sans h-screen relative"> <!-- body ahora es relative -->

    <!-- Pantalla de LOGIN (fixed) -->
    <div id="login-screen" class="absolute inset-0 bg-gray-800 flex items-center justify-center z-50">
        <div class="bg-gray-900 p-8 rounded-xl shadow-2xl w-11/12 md:w-96 text-center">
            <h2 class="text-3xl font-bold text-blue-400 mb-6">Iniciar Sesión</h2>
            <p class="text-gray-400 mb-6">Accede como vendedor usando tu EID.</p>

            <div class="mb-4 text-left">
                <label for="username-input" class="block text-gray-300 text-sm mb-1">Usuario (EID: E001, E002...)</label>
                <input type="text" id="username-input" placeholder="E001"
                       class="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-blue-500 focus:border-blue-500"
                       onkeypress="if(event.key === 'Enter') document.getElementById('password-input').focus()">
            </div>

            <div class="mb-6 text-left">
                <label for="password-input" class="block text-gray-300 text-sm mb-1">Contraseña</label>
                <input type="password" id="password-input" placeholder="Contraseña"
                       class="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-blue-500 focus:border-blue-500"
                       onkeypress="if(event.key === 'Enter') handleLogin()">
            </div>
            
            <button onclick="handleLogin()" class="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg shadow-md">
                ACCEDER AL TPV
            </button>
        </div>
    </div>

    <!-- Pantalla POS Principal (Ocupa todo el espacio) -->
    <div id="pos-screen" class="absolute inset-0 flex flex-col overflow-hidden hidden"> 
        
        <!-- Header (Fixed Top) -->
        <header class="bg-gray-800 p-4 shadow-lg flex justify-between items-center flex-shrink-0 w-full">
            <h1 class="text-xl font-extrabold text-blue-400">POS Boutique Móvil</h1>
            <div class="flex items-center space-x-4">
                <span id="user-display" class="text-sm text-gray-300">Usuario: ANÓNIMO</span>
                <button onclick="handleLogout()" class="text-sm bg-red-600 px-3 py-1 rounded-full hover:bg-red-700 text-white font-bold">
                    Salir
                </button>
            </div>
        </header>

        <!-- Main Content Area (Layout Flex) -->
        <div class="flex-1 flex flex-col md:flex-row overflow-hidden">
            
            <!-- Left Panel: Product Search & Customer -->
            <div class="w-full md:w-1/3 bg-gray-800 p-4 flex flex-col flex-shrink-0">
                
                <div class="mb-4">
                    <label for="customer-name" class="block text-gray-400 text-sm mb-1">Cliente (Opcional)</label>
                    <input type="text" id="customer-name" placeholder="Público General"
                           class="w-full p-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-blue-500 focus:border-blue-500">
                </div>

                <div class="mb-4">
                    <label for="product-input" class="block text-gray-400 text-sm mb-1">Escanear Producto / Buscar SKU</label>
                    <input type="text" id="product-input" placeholder="Cargando inventario..."
                           class="w-full p-3 text-xl bg-gray-700 border border-blue-500 rounded-lg text-white focus:ring-blue-500 focus:border-blue-500 font-mono"
                           onkeypress="handleProductInput(event)">
                </div>
                
                <!-- Quick Action Buttons (Add other features here) -->
                <div class="grid grid-cols-2 gap-2 mt-auto pt-4 border-t border-gray-700">
                     <button onclick="openInventorySearchModal()" class="py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-white font-bold shadow-md text-sm">
                        Buscar Inventario
                    </button>
                </div>
            </div>

            <!-- Right Panel: Cart and Totals -->
            <div class="w-full md:w-2/3 flex flex-col bg-gray-700 overflow-hidden">
                
                <!-- Cart List -->
                <div class="p-4 flex-1 overflow-y-auto">
                    <h2 class="text-xl font-bold mb-4 text-blue-300">Carrito de Compras</h2>
                    <ul id="cart-list" class="space-y-1">
                        <!-- Items will be inserted here -->
                    </ul>
                    <p class="text-gray-400 mt-4 text-center" id="empty-cart-msg">Añade productos para empezar.</p>
                </div>

                <!-- Totals and Payment Button (Fixed Bottom of the Right Panel) -->
                <div class="bg-gray-800 p-4 flex-shrink-0 shadow-2xl">
                    <div class="flex justify-between items-center mb-3">
                        <span class="text-2xl font-bold text-gray-200">Subtotal:</span>
                        <span class="text-3xl font-extrabold text-yellow-400" id="subtotal-display">$0.00</span>
                    </div>
                    
                    <button onclick="openPaymentModal()" class="w-full py-4 bg-green-600 hover:bg-green-700 text-white font-bold rounded-xl shadow-lg transform hover:scale-[1.01] transition duration-150 ease-in-out">
                        PAGAR Y FINALIZAR VENTA
                    </button>
                </div>
            </div>
        </div>
    </div>
    
    <!-- --- Modales (Resto del código) --- -->
    
    <!-- --- Modal for Item Options (Modify/Remove) --- -->
    <div id="modal-overlay" class="hidden fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
        <div class="bg-gray-800 p-6 rounded-xl shadow-2xl w-11/12 md:w-1/3">
            <div id="modal-content">
                <!-- Content injected by JavaScript -->
            </div>
            <button onclick="closeModal()" class="mt-4 w-full py-2 bg-gray-600 hover:bg-gray-500 text-white font-bold rounded-lg">
                Cancelar
            </button>
        </div>
    </div>

    <!-- --- Modal para Búsqueda de Inventario --- -->
    <div id="inventory-search-modal-overlay" class="hidden fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
        <div class="bg-gray-800 p-6 rounded-xl shadow-2xl w-11/12 md:w-2/3">
            <h3 class="text-xl font-bold mb-4 text-white">Buscar Stock en Inventario</h3>
            <div class="flex space-x-2 mb-4">
                <input type="text" id="inventory-search-input" placeholder="Buscar por Nombre o SKU..."
                       class="flex-1 p-2 bg-gray-700 border border-gray-600 rounded text-white">
                <button onclick="searchInventory()" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg">
                    Buscar
                </button>
            </div>
            <div id="inventory-results" class="max-h-80 overflow-y-auto bg-gray-700 p-3 rounded-lg border border-gray-600">
                <p class="text-gray-400">Ingrese un término para buscar.</p>
                <!-- Resultados se inyectan aquí -->
            </div>
            <button onclick="closeInventorySearchModal()" class="mt-4 w-full py-2 bg-gray-600 hover:bg-gray-500 text-white font-bold rounded-lg">
                Cerrar
            </button>
        </div>
    </div>

    <!-- --- Modal for Payment --- -->
    <div id="payment-overlay" class="hidden fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
        <div class="bg-gray-800 p-6 rounded-xl shadow-2xl w-11/12 md:w-1/3">
            <button onclick="closePaymentModal()" class="float-right text-gray-400 hover:text-white">&times;</button>
            <div id="payment-modal-content" class="mt-4">
                <!-- Payment fields injected by JavaScript -->
            </div>
        </div>
    </div>

    <!-- --- Modal Post-Venta --- -->
    <div id="post-sale-overlay" class="hidden fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
        <div class="bg-gray-800 p-6 rounded-xl shadow-2xl w-11/12 md:w-1/3">
            <div id="post-sale-content" class="mt-4 text-center">
                <!-- Opciones de impresión/correo inyectadas por JavaScript -->
            </div>
        </div>
    </div>
    
    <!-- --- Floating Message Box --- -->
    <div id="message-box" class="fixed bottom-4 left-1/2 transform -translate-x-1/2 p-3 rounded-lg text-white font-bold shadow-xl opacity-0 transition-opacity duration-300 pointer-events-none">
    </div>

    

    <!-- [NUEVO] Área oculta para inyectar el contenido del ticket antes de imprimir -->
    <div id="print-area" class="ticket-print-area hidden"></div>

</body>
</html>
