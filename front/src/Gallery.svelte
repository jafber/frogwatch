<script>
    import { onMount } from 'svelte';

    // dates like "2026-07-06", newest first; photo at /photos/<date>.jpg
    let dates = $state([]);

    onMount(async () => {
        try {
            const res = await fetch('/photos/index.json');
            if (!res.ok) return;
            const data = await res.json();
            if (Array.isArray(data)) {
                dates = data.slice().sort().reverse();
            }
        } catch {
            // no gallery yet: hide section
        }
    });
</script>

{#if dates.length > 0}
    <section>
        <h2>Frosch des Tages</h2>
        <div class="grid">
            {#each dates as date (date)}
                <figure>
                    <a href="/photos/{date}.jpg" target="_blank" rel="noopener">
                        <img src="/photos/{date}.jpg" alt="Frosch am {date}" loading="lazy" />
                    </a>
                    <figcaption>{date}</figcaption>
                </figure>
            {/each}
        </div>
    </section>
{/if}

<style>
    h2 {
        color: var(--green);
        font-size: 1.25rem;
        margin-bottom: 0.75rem;
    }

    .grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
        gap: 0.75rem;
    }

    img {
        display: block;
        width: 100%;
        aspect-ratio: 16 / 9;
        object-fit: cover;
        border-radius: 0.375rem;
        background-color: #eee;
    }

    figcaption {
        font-size: 0.75rem;
        color: #555;
        margin-top: 0.25rem;
        text-align: center;
    }
</style>
