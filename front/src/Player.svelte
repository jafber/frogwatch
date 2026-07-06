<script>
    import { onMount } from 'svelte';
    import 'media-chrome';

    let { src } = $props();

    let video;
    let offline = $state(false);

    const REINIT_DELAY_MS = 10000;
    const MAX_NETWORK_RETRY_MS = 30000;
    const LIVE_EDGE_TOLERANCE_S = 5;

    onMount(() => {
        let hls = null;
        let retryDelay = 1000;
        let timer = null;
        let destroyed = false;

        // Twitch behavior: un-pausing returns to the live edge instead of
        // resuming seconds behind
        video.addEventListener('play', () => {
            if (hls && hls.liveSyncPosition &&
                video.currentTime < hls.liveSyncPosition - LIVE_EDGE_TOLERANCE_S) {
                video.currentTime = hls.liveSyncPosition;
            }
        });

        // full teardown + fresh manifest load; hls.startLoad() alone does not
        // recover from a fatal manifest error (stream down = 404 manifest)
        const scheduleReinit = () => {
            offline = true;
            if (hls) {
                hls.destroy();
                hls = null;
            }
            timer = setTimeout(init, retryDelay);
            retryDelay = Math.min(retryDelay * 2, MAX_NETWORK_RETRY_MS);
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
                        video.play().catch(() => {});
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
            hls.on(Hls.Events.MANIFEST_PARSED, () => {
                // stream came (back) online: resume playback (muted, allowed)
                video.play().catch(() => {});
            });
            hls.on(Hls.Events.FRAG_LOADED, () => {
                offline = false;
                retryDelay = 1000;
            });
            hls.on(Hls.Events.ERROR, (_event, data) => {
                if (!data.fatal) return;
                offline = true;
                if (data.type === Hls.ErrorTypes.MEDIA_ERROR) {
                    hls.recoverMediaError();
                } else {
                    // network (publisher gone, manifest 404) or other fatal:
                    // tear down and re-init with backoff until it's back
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

<!-- keysused: play/pause + fullscreen hotkeys only, no arrow-key seeking -->
<media-controller autohide="2" keysused="Space k f">
    <!-- svelte-ignore a11y_media_has_caption -->
    <video slot="media" bind:this={video} autoplay muted playsinline></video>
    {#if offline}
        <div slot="centered-chrome" class="overlay">
            <!-- 90-ring spinner from https://github.com/n3r4zzurr0/svg-spinners (MIT) -->
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-label="Stream offline – wir verbinden neu">
                <path
                    class="ring"
                    d="M10.14,1.16a11,11,0,0,0-9,8.92A1.59,1.59,0,0,0,2.46,12,1.52,1.52,0,0,0,4.11,10.7a8,8,0,0,1,6.66-6.61A1.42,1.42,0,0,0,12,2.69h0A1.57,1.57,0,0,0,10.14,1.16Z"
                />
            </svg>
        </div>
    {/if}
    <media-control-bar>
        {#if !offline}
            <media-play-button></media-play-button>
        {/if}
        <span class="spacer"></span>
        <media-fullscreen-button></media-fullscreen-button>
    </media-control-bar>
</media-controller>

<style>
    media-controller {
        display: block;
        width: 100%;
        aspect-ratio: 4 / 3;
        border-radius: 0.5rem;
        overflow: hidden;
        background-color: black;
        --media-icon-color: white;
        --media-control-background: transparent;
        --media-control-hover-background: rgba(0, 100, 0, 0.6);
    }

    video {
        width: 100%;
        height: 100%;
    }

    media-control-bar {
        width: 100%;
        padding: 0.5rem 0.75rem;
        background: linear-gradient(transparent, rgba(0, 0, 0, 0.7));
    }

    .spacer {
        flex-grow: 1;
    }

    .overlay {
        pointer-events: none;
        line-height: 0;
    }

    .overlay svg {
        width: 3rem;
        height: 3rem;
        fill: white;
    }

    .ring {
        transform-origin: center;
        animation: spin 0.75s infinite linear;
    }

    @keyframes spin {
        100% {
            transform: rotate(360deg);
        }
    }
</style>
