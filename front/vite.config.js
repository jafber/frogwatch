import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
    plugins: [svelte()],
    server: {
        // local dev against the compose stack (docker-compose.local.yml)
        proxy: {
            '/stream': 'http://localhost:8080',
            '/photos': 'http://localhost:8080',
        },
    },
});
