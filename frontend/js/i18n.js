/**
 * i18n.js - Sistema de Internacionalización
 * Soporta: Español (ES), English (EN), 日本語 (JP)
 */

const i18n = {
    currentLanguage: localStorage.getItem('language') || 'es',
    
    translations: {
        es: {
            // Menu
            dashboard: 'Dashboard',
            camaras: 'Cámaras',
            personas: 'Personas',
            vehiculos: 'Vehículos',
            alertas: 'Alertas',
            baseDatos: 'Base de Datos',
            reportes: 'Reportes',
            deteccionVivo: 'Detección en Vivo',
            diagnostico: 'Diagnóstico',
            cerrarSesion: 'Cerrar Sesión',
            
            // Panel
            panel: 'Panel',
            
            // Dashboard
            conectarCliente: 'Conectar Cliente',
            accesoRemoto: 'ACCESO REMOTO',
            accesoLocal: 'ACCESO LOCAL',
            copiar: 'Copiar',
            
            // Stats
            estadisticas: 'Estadísticas',
            camarasActivas: 'Cámaras Activas',
            personasDetectadas: 'Personas Detectadas',
            vehiculosDetectados: 'Vehículos Detectados',
            alertasActivas: 'Alertas Activas',
            
            // Gráficos
            deteccionesPorTipo: 'Detecciones por Tipo',
            vehiculosDetectados: 'Vehículos Detectados',
            estadoDelSistema: 'Estado del Sistema',
            ultimasDetecciones: 'Últimas Detecciones',
            
            // Botones
            actualizar: 'Actualizar datos',
            toggleDarkMode: 'Alternar modo oscuro',
            
            // Modo oscuro
            modoClaro: 'Modo Claro',
            modoOscuro: 'Modo Oscuro',
            
            // Idioma
            idioma: 'Idioma',
            
            // Horas
            hace: 'Hace',
            minutos: 'minutos',
            horas: 'horas',
            dias: 'días',

            // Camara Cliente
            camaraClienteTitle: 'Camara Cliente',
            inactivo: 'Inactivo',
            transmitiendo: 'Transmitiendo',
            idCamara: 'ID de cámara',
            camaraLabel: 'Cámara',
            frontal: 'Frontal',
            trasera: 'Trasera',
            calidadJpeg: 'Calidad JPEG',
            fpsObjetivo: 'FPS objetivo',
            iniciarTransmision: 'Iniciar transmisión',
            cambiarCamara: 'Cambiar cámara',
            detener: 'Detener',
            framesEnviados: 'Frames enviados',
            fpsReal: 'FPS real',
            kbEnviados: 'KB enviados',
            errores: 'Errores',
            esperando: 'Esperando...',
            httpsRequerido: 'HTTPS requerido',
            errorSinSoporte: 'Error: sin soporte',
            errorCamara: 'Error cámara',
            streamIniciado: 'Stream iniciado',
            streamDetenido: 'Stream detenido',
            httpsWarningTitle: '⚠️ Se requiere HTTPS para acceder a la cámara',
            httpsWarningBody: 'Tu navegador bloquea el acceso a la cámara en conexiones HTTP desde IPs de red.',
            httpsWarningSolLabel: 'Soluciones:',
            httpsWarningSol1: 'Conecta el dispositivo al mismo PC por USB y abre',
            httpsWarningSol2: 'O configura HTTPS con certificado en el servidor.',
            httpsWarningTech: 'Error técnico: contexto no seguro (isSecureContext = false)',
            permisoDenegado: 'Permiso denegado. Permite el acceso a la cámara en el navegador.',
            camaraNoEncontrada: 'No se encontró ninguna cámara en este dispositivo.',
            camaraEnUso: 'La cámara está siendo usada por otra aplicación.',
            errorGetUserMedia: 'getUserMedia no disponible. Abre esta página en HTTPS o desde localhost.',
            errorHttp: 'Error HTTP ',
            errorRed: 'Error red: ',
        },
        en: {
            // Menu
            dashboard: 'Dashboard',
            camaras: 'Cameras',
            personas: 'People',
            vehiculos: 'Vehicles',
            alertas: 'Alerts',
            baseDatos: 'Database',
            reportes: 'Reports',
            deteccionVivo: 'Live Detection',
            diagnostico: 'Diagnostic',
            cerrarSesion: 'Logout',
            
            // Panel
            panel: 'Panel',
            
            // Dashboard
            conectarCliente: 'Connect Client',
            accesoRemoto: 'REMOTE ACCESS',
            accesoLocal: 'LOCAL ACCESS',
            copiar: 'Copy',
            
            // Stats
            estadisticas: 'Statistics',
            camarasActivas: 'Active Cameras',
            personasDetectadas: 'People Detected',
            vehiculosDetectados: 'Vehicles Detected',
            alertasActivas: 'Active Alerts',
            
            // Gráficos
            deteccionesPorTipo: 'Detections by Type',
            vehiculosDetectados: 'Vehicles Detected',
            estadoDelSistema: 'System Status',
            ultimasDetecciones: 'Latest Detections',
            
            // Botones
            actualizar: 'Refresh data',
            toggleDarkMode: 'Toggle dark mode',
            
            // Modo oscuro
            modoClaro: 'Light Mode',
            modoOscuro: 'Dark Mode',
            
            // Idioma
            idioma: 'Language',
            
            // Horas
            hace: 'ago',
            minutos: 'minutes',
            horas: 'hours',
            dias: 'days',

            // Camara Cliente
            camaraClienteTitle: 'Camera Client',
            inactivo: 'Inactive',
            transmitiendo: 'Streaming',
            idCamara: 'Camera ID',
            camaraLabel: 'Camera',
            frontal: 'Front',
            trasera: 'Rear',
            calidadJpeg: 'JPEG Quality',
            fpsObjetivo: 'Target FPS',
            iniciarTransmision: 'Start Stream',
            cambiarCamara: 'Flip Camera',
            detener: 'Stop',
            framesEnviados: 'Frames Sent',
            fpsReal: 'Actual FPS',
            kbEnviados: 'KB Sent',
            errores: 'Errors',
            esperando: 'Waiting...',
            httpsRequerido: 'HTTPS required',
            errorSinSoporte: 'Error: not supported',
            errorCamara: 'Camera error',
            streamIniciado: 'Stream started',
            streamDetenido: 'Stream stopped',
            httpsWarningTitle: '⚠️ HTTPS required to access the camera',
            httpsWarningBody: 'Your browser blocks camera access over HTTP from network IPs.',
            httpsWarningSolLabel: 'Solutions:',
            httpsWarningSol1: 'Connect the device to the same PC via USB and open',
            httpsWarningSol2: 'Or configure HTTPS with a certificate on the server.',
            httpsWarningTech: 'Technical error: insecure context (isSecureContext = false)',
            permisoDenegado: 'Permission denied. Allow camera access in the browser.',
            camaraNoEncontrada: 'No camera found on this device.',
            camaraEnUso: 'The camera is being used by another application.',
            errorGetUserMedia: 'getUserMedia not available. Open this page over HTTPS or from localhost.',
            errorHttp: 'HTTP Error ',
            errorRed: 'Network error: ',
        },
        jp: {
            // Menu
            dashboard: 'ダッシュボード',
            camaras: 'カメラ',
            personas: '人物',
            vehiculos: '車両',
            alertas: 'アラート',
            baseDatos: 'データベース',
            reportes: 'レポート',
            deteccionVivo: 'ライブ検出',
            diagnostico: '診断',
            cerrarSesion: 'ログアウト',
            
            // Panel
            panel: 'パネル',
            
            // Dashboard
            conectarCliente: 'クライアント接続',
            accesoRemoto: 'リモートアクセス',
            accesoLocal: 'ローカルアクセス',
            copiar: 'コピー',
            
            // Stats
            estadisticas: '統計',
            camarasActivas: 'アクティブなカメラ',
            personasDetectadas: '検出された人物',
            vehiculosDetectados: '検出された車両',
            alertasActivas: 'アクティブなアラート',
            
            // Gráficos
            deteccionesPorTipo: 'タイプ別検出',
            vehiculosDetectados: '検出された車両',
            estadoDelSistema: 'システムステータス',
            ultimasDetecciones: '最新の検出',
            
            // Botones
            actualizar: 'データを更新',
            toggleDarkMode: 'ダークモードを切り替え',
            
            // Modo oscuro
            modoClaro: 'ライトモード',
            modoOscuro: 'ダークモード',
            
            // Idioma
            idioma: '言語',
            
            // Horas
            hace: '前',
            minutos: '分',
            horas: '時間',
            dias: '日',

            // Camara Cliente
            camaraClienteTitle: 'カメラクライアント',
            inactivo: '非アクティブ',
            transmitiendo: '配信中',
            idCamara: 'カメラID',
            camaraLabel: 'カメラ',
            frontal: 'フロント',
            trasera: 'リア',
            calidadJpeg: 'JPEG品質',
            fpsObjetivo: '目標FPS',
            iniciarTransmision: '配信開始',
            cambiarCamara: 'カメラ切替',
            detener: '停止',
            framesEnviados: '送信フレーム',
            fpsReal: '実際のFPS',
            kbEnviados: '送信KB',
            errores: 'エラー',
            esperando: '待機中...',
            httpsRequerido: 'HTTPSが必要',
            errorSinSoporte: 'エラー: 非対応',
            errorCamara: 'カメラエラー',
            streamIniciado: '配信を開始しました',
            streamDetenido: '配信を停止しました',
            httpsWarningTitle: '⚠️ カメラにアクセスするにはHTTPSが必要です',
            httpsWarningBody: 'ブラウザはネットワークIPのHTTP接続でカメラアクセスをブロックします。',
            httpsWarningSolLabel: '解決策:',
            httpsWarningSol1: 'デバイスをUSBで同じPCに接続して開いてください',
            httpsWarningSol2: 'またはサーバーに証明書でHTTPSを設定してください。',
            httpsWarningTech: '技術エラー: 安全でないコンテキスト (isSecureContext = false)',
            permisoDenegado: '権限が拒否されました。ブラウザでカメラアクセスを許可してください。',
            camaraNoEncontrada: 'このデバイスにカメラが見つかりません。',
            camaraEnUso: 'カメラは別のアプリで使用中です。',
            errorGetUserMedia: 'getUserMediaが利用できません。HTTPSまたはlocalhostから開いてください。',
            errorHttp: 'HTTPエラー ',
            errorRed: 'ネットワークエラー: ',
        }
    },
    
    /**
     * Obtener traducción
     */
    t(key) {
        const translation = this.translations[this.currentLanguage]?.[key];
        if (!translation) {
            console.warn(`Translation missing: ${key} for language ${this.currentLanguage}`);
            return key;
        }
        return translation;
    },
    
    /**
     * Cambiar idioma
     */
    setLanguage(lang) {
        if (this.translations[lang]) {
            this.currentLanguage = lang;
            localStorage.setItem('language', lang);
            this.updatePageTranslations();
            console.log(`[i18n] Language changed to: ${lang}`);
        } else {
            console.warn(`[i18n] Language not supported: ${lang}`);
        }
    },
    
    /**
     * Actualizar todas las traducciones en la página
     */
    updatePageTranslations() {
        // Actualizar todos los elementos con data-i18n
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            element.textContent = this.t(key);
        });
        
        // Actualizar todos los atributos placeholder
        document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
            const key = element.getAttribute('data-i18n-placeholder');
            element.placeholder = this.t(key);
        });
        
        // Actualizar todos los atributos title
        document.querySelectorAll('[data-i18n-title]').forEach(element => {
            const key = element.getAttribute('data-i18n-title');
            element.title = this.t(key);
        });
        
        // Disparar evento para que otros scripts sepan que se actualizaron las traducciones
        window.dispatchEvent(new CustomEvent('languageChanged', { detail: { language: this.currentLanguage } }));
    },
    
    /**
     * Inicializar i18n
     */
    init() {
        console.log(`[i18n] Inicializando con idioma: ${this.currentLanguage}`);
        this.updatePageTranslations();
        
        // Escuchar cambios de idioma
        document.addEventListener('DOMContentLoaded', () => {
            this.updatePageTranslations();
        });
    }
};

// Inicializar cuando se cargue el script
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        i18n.init();
    });
} else {
    i18n.init();
}

console.log('[Scripts] i18n.js cargado ✓');
