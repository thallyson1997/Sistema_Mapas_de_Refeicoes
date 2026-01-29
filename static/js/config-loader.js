// Script global para aplicar configurações do sistema
// Este script deve ser incluído em todas as páginas

(function() {
    'use strict';
    
    // Aplicar modo escuro IMEDIATAMENTE (antes do DOM carregar)
    const darkMode = localStorage.getItem('sgmrp_dark_mode') === 'true';
    if (darkMode) {
        document.documentElement.classList.add('dark-mode');
        if (document.body) {
            document.body.classList.add('dark-mode');
        }
    }
    
    // Garantir aplicação quando o DOM carregar
    document.addEventListener('DOMContentLoaded', function() {
        const darkMode = localStorage.getItem('sgmrp_dark_mode') === 'true';
        if (darkMode) {
            document.body.classList.add('dark-mode');
        }
    });
})();
