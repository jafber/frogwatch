<script>
    import { onMount } from 'svelte';

    let { src } = $props();

    let video;
    let offline = $state(false);

    const REINIT_DELAY_MS = 10000;
    const MAX_NETWORK_RETRY_MS = 30000;

    onMount(() => {
        let hls = null;
        let retryDelay = 1000;
        let timer = null;
        let destroyed = false;

        const scheduleReinit = () => {
            offline = true;
            if (hls) {
                hls.destroy();
                hls = null;
            }
            timer = setTimeout(init, REINIT_DELAY_MS);
        };

        const init = async () => {
            if (destroyed) return;
            if (video.canPlayType('application/vnd.apple.mpegurl')) {
                // Safari: native HLS. Recover by reloading the source on error.
                video.src = src;
                video.addEventListener('error', () => {
                    offline = true;
                    timer = setTimeout(() => {
                        video.src = src;
                        video.load();
                    }, REINIT_DELAY_MS);
                });
                video.addEventListener('playing', () => (offline = false));
                return;
            }
            const { default: Hls } = await import('hls.js');
            if (destroyed) return;
            if (!Hls.isSupported()) {
                offline = true;
                return;
            }
            hls = new Hls({
                // live stream: show LIVE instead of a growing duration,
                // and evict footage >30s behind the playhead (RAM cap)
                liveDurationInfinity: true,
                backBufferLength: 30,
            });
            hls.loadSource(src);
            hls.attachMedia(video);
            hls.on(Hls.Events.FRAG_LOADED, () => {
                offline = false;
                retryDelay = 1000;
            });
            hls.on(Hls.Events.ERROR, (_event, data) => {
                if (!data.fatal) return;
                offline = true;
                if (data.type === Hls.ErrorTypes.NETWORK_ERROR) {
                    // e.g. publisher gone, manifest 404: retry with backoff
                    timer = setTimeout(() => {
                        if (hls) hls.startLoad();
                    }, retryDelay);
                    retryDelay = Math.min(retryDelay * 2, MAX_NETWORK_RETRY_MS);
                } else if (data.type === Hls.ErrorTypes.MEDIA_ERROR) {
                    hls.recoverMediaError();
                } else {
                    scheduleReinit();
                }
            });
        };

        init();

        return () => {
            destroyed = true;
            clearTimeout(timer);
            if (hls) hls.destroy();
        };
    });
</script>

<div class="player">
    <!-- svelte-ignore a11y_media_has_caption -->
    <video bind:this={video} controls autoplay muted playsinline></video>
    {#if offline}
        <div class="overlay">Stream offline &ndash; wir verbinden neu&hellip;</div>
    {/if}
</div>

<style>
    .player {
        position: relative;
        background-color: var(--green);
        border-radius: 0.5rem;
        overflow: hidden;
    }

    video {
        display: block;
        width: 100%;
        aspect-ratio: 4 / 3;
        background-color: black;
    }

    .overlay {
        position: absolute;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        background-color: rgba(0, 40, 0, 0.7);
        font-size: 1.1rem;
        pointer-events: none;
    }
</style>
