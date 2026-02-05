// Script global para aplicar configurações do sistema
// Este script deve ser incluído em todas as páginas

(function() {
    'use strict';
    
    // Função auxiliar para aplicar/atualizar classes de densidade
    function applyDensity(density) {
        const root = document.documentElement;
        const body = document.body;

        const DENSITY_CLASSES = ['density-compact', 'density-normal', 'density-comfortable'];

        DENSITY_CLASSES.forEach(cls => {
            root.classList.remove(cls);
            if (body) {
                body.classList.remove(cls);
            }
        });

        let targetClass = null;
        if (density === 'compacta') {
            targetClass = 'density-compact';
        } else if (density === 'normal') {
            targetClass = 'density-normal';
        } else if (density === 'confortavel') {
            targetClass = 'density-comfortable';
        }

        if (targetClass) {
            root.classList.add(targetClass);
            if (body) {
                body.classList.add(targetClass);
            }
        }
    }

    // Função auxiliar para aplicar/atualizar classes de tamanho de fonte
    function applyFontSize(size) {
        const root = document.documentElement;
        const body = document.body;

        const FONT_CLASSES = ['font-small', 'font-normal', 'font-large'];

        FONT_CLASSES.forEach(cls => {
            root.classList.remove(cls);
            if (body) {
                body.classList.remove(cls);
            }
        });

        let targetClass = null;
        if (size === 'pequena') {
            targetClass = 'font-small';
        } else if (size === 'normal') {
            targetClass = 'font-normal';
        } else if (size === 'grande') {
            targetClass = 'font-large';
        }

        if (targetClass) {
            root.classList.add(targetClass);
            if (body) {
                body.classList.add(targetClass);
            }
        }
    }

    // Aplicar modo escuro IMEDIATAMENTE (antes do DOM carregar)
    const darkMode = localStorage.getItem('sgmrp_dark_mode') === 'true';
    if (darkMode) {
        document.documentElement.classList.add('dark-mode');
        if (document.body) {
            document.body.classList.add('dark-mode');
        }
    }

    // Aplicar densidade IMEDIATAMENTE
    const densidade = localStorage.getItem('sgmrp_densidade') || 'normal';
    applyDensity(densidade);

    // Aplicar tamanho de fonte IMEDIATAMENTE
    const tamanhoFonte = localStorage.getItem('sgmrp_tamanho_fonte') || 'normal';
    applyFontSize(tamanhoFonte);

    // Garantir aplicação quando o DOM carregar (caso body ainda não exista antes)
    document.addEventListener('DOMContentLoaded', function() {
        const darkModeAtivo = localStorage.getItem('sgmrp_dark_mode') === 'true';
        if (darkModeAtivo) {
            document.body.classList.add('dark-mode');
        }

        const densidadeAtual = localStorage.getItem('sgmrp_densidade') || 'normal';
        applyDensity(densidadeAtual);

        const tamanhoFonteAtual = localStorage.getItem('sgmrp_tamanho_fonte') || 'normal';
        applyFontSize(tamanhoFonteAtual);
    });
})();
