import api from './axios';

export const servicios = {
    // --- 1. AUTENTICACIÓN ---
    auth: {
        login: async (username, password) => {
            const response = await api.post('/auth/jwt/create/', { username, password });
            return response.data;
        },
        register: (datos) => api.post('/auth/users/', datos),
        getPerfil: () => api.get('/api/perfil/me/'),
        updatePerfil: (datos) => api.patch('/api/perfil/me/', datos),
        logout: () => {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
        }
    },

    // --- 2. GESTIÓN DE REPORTES (Ciudadano y Gobierno) ---
    reportes: {
        getAll: () => api.get('/api/reportes/'),
        getMisReportes: () => api.get('/api/reportes/mis_solicitudes/'),
        crear: (formData) => api.post('/api/reportes/', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        }),
        validar: (id) => api.post(`/api/reportes/${id}/validar/`),
        gestionar: (id, formData) => api.patch(`/api/reportes/${id}/`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        })
    },

    // --- 3. RECURSOS DE GOBIERNO (PIPAS) ---
    pipas: {
        getAll: () => api.get('/api/pipas/'),
    },

    // --- 4. INFORMACIÓN PÚBLICA ---
    publico: {
        getNoticias: () => api.get('/api/noticias/'),
        getPozos: () => api.get('/api/pozos/'),
    },

    // --- 5. INTELIGENCIA (DASHBOARD) ---
    admin: {
        getEstadisticas:        () => api.get('/api/dashboard/resumen/'),
        getGraficaSemanal:      () => api.get('/api/dashboard/historial_semanal/'),
        getTasaResolucion:      () => api.get('/api/dashboard/tasa_resolucion/'),
        getTiempoResolucion:    () => api.get('/api/dashboard/tiempo_resolucion/'),
        getZonasCalor:          () => api.get('/api/dashboard/zonas_calor/'),
        getEficienciaPipas:     () => api.get('/api/dashboard/eficiencia_pipas/'),
        getReportesRecurrentes: () => api.get('/api/dashboard/reportes_recurrentes/'),
        urlExportar: 'http://localhost:8000/api/dashboard/exportar_reportes/'
    }
};
