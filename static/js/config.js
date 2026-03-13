const API_BASE_URL = {
    development: "http://127.0.0.1:5000",
    production: "https://saraswati-library.onrender.com"
};

const isProduction = window.location.hostname !== "127.0.0.1" && 
                     window.location.hostname !== "localhost";

const API_URL = isProduction ? API_BASE_URL.production : API_BASE_URL.development;

window.API_URL = API_URL;