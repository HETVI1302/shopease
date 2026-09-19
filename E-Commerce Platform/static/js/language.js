const translations = {
    en: {
        search_placeholder: "Search products...",
        shop_all: "Shop All",
        categories: "Categories",
        admin_dashboard: "Admin Dashboard",
        delivery_dashboard: "Delivery Dashboard",
        my_orders: "My Orders",
        logout: "Logout",
        login: "Login",
        register: "Register",
        login_subtitle: "Sign in to your account",
        dont_have_account: "Don't have an account?",
        
        // Register Page
        register_title: "Join ShopEase",
        register_subtitle: "Create your account to continue",
        role_select: "I am a...",
        role_customer: "Customer (Shopper)",
        role_seller: "Seller (Store Admin)",
        role_delivery: "Delivery Partner (Rider)",
        first_name: "First Name",
        last_name: "Last Name",
        username: "Username",
        email: "Email Address",
        password: "Password",
        delivery_details: "Delivery Partner Details",
        phone_number: "Phone Number (e.g. 9876543210)",
        vehicle_number: "Vehicle Reg. (e.g. MH-01-AB-1234)",
        register_btn: "Register Now",
        already_have_account: "Already have an account?",
        login_here: "Login here",

        // Delivery Dashboard
        accept_order: "Accept Order",
        out_for_delivery: "Out for Delivery",
        confirm_delivered: "Confirm Delivered",
        no_active_deliveries: "No active deliveries right now.",
        completed_deliveries: "Completed Deliveries",
        active_deliveries: "Active Deliveries",
    },
    hi: {
        search_placeholder: "उत्पाद खोजें...",
        shop_all: "सभी देखें",
        categories: "श्रेणियाँ",
        admin_dashboard: "व्यवस्थापक डैशबोर्ड",
        delivery_dashboard: "डिलीवरी डैशबोर्ड",
        my_orders: "मेरे ऑर्डर",
        logout: "लॉग आउट",
        login: "लॉग इन",
        register: "रजिस्टर करें",
        login_subtitle: "अपने खाते में साइन इन करें",
        dont_have_account: "क्या आपके पास खाता नहीं है?",
        
        // Register Page
        register_title: "ShopEase से जुड़ें",
        register_subtitle: "आगे बढ़ने के लिए अपना खाता बनाएं",
        role_select: "मैं एक हूँ...",
        role_customer: "ग्राहक (खरीदार)",
        role_seller: "विक्रेता (स्टोर व्यवस्थापक)",
        role_delivery: "डिलीवरी पार्टनर (राइडर)",
        first_name: "पहला नाम",
        last_name: "अंतिम नाम",
        username: "उपयोगकर्ता नाम",
        email: "ईमेल पता",
        password: "पासवर्ड",
        delivery_details: "डिलीवरी पार्टनर विवरण",
        phone_number: "फ़ोन नंबर",
        vehicle_number: "वाहन पंजीकरण संख्या",
        register_btn: "अभी रजिस्टर करें",
        already_have_account: "क्या आपके पास पहले से खाता है?",
        login_here: "यहाँ लॉग इन करें",

        // Delivery Dashboard
        accept_order: "ऑर्डर स्वीकार करें",
        out_for_delivery: "डिलीवरी के लिए निकल गया",
        confirm_delivered: "डिलीवरी की पुष्टि करें",
        no_active_deliveries: "अभी कोई सक्रिय डिलीवरी नहीं है।",
        completed_deliveries: "पूरी की गई डिलीवरी",
        active_deliveries: "सक्रिय डिलीवरी",
    }
};

function setLanguage(lang) {
    localStorage.setItem('shopease_lang', lang);
    applyLanguage(lang);
}

function applyLanguage(lang) {
    const dict = translations[lang] || translations['en'];
    
    // Update elements with data-i18n text
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (dict[key]) {
            el.innerText = dict[key];
        }
    });

    // Update elements with data-i18n-placeholder
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (dict[key]) {
            el.setAttribute('placeholder', dict[key]);
        }
    });

    // Update active state of language toggle buttons if they exist
    const langBtns = document.querySelectorAll('.lang-btn');
    if(langBtns.length > 0) {
        langBtns.forEach(btn => {
            if(btn.innerText.toLowerCase() === lang) {
                btn.classList.add('fw-bold');
                btn.classList.remove('text-muted');
            } else {
                btn.classList.remove('fw-bold');
                btn.classList.add('text-muted');
            }
        });
    }
}

// Auto-run on DOM content loaded
document.addEventListener('DOMContentLoaded', () => {
    const savedLang = localStorage.getItem('shopease_lang') || 'en';
    applyLanguage(savedLang);
});
