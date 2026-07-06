<script>
    import Player from './Player.svelte';
    import Gallery from './Gallery.svelte';
</script>

<header>
    <h1>Froschkamera</h1>
    <img alt="" src="/img/logo.png" />
</header>

<main>
    <Player src="/stream/frog/index.m3u8" />
    <Gallery />
</main>

<footer>
    <a href="https://jan-berndt.de/pages/impressum">Impressum</a>
    <a href="https://jan-berndt.de/pages/datenschutz">Datenschutz</a>
</footer>

<style>
    header {
        /* no bottom padding: the frog logo sits flush on top of the player */
        padding: 1rem 1rem 0;
        display: flex;
        justify-content: space-between;
        align-items: end;
        max-width: 60rem;
        margin: 0 auto;
    }

    h1 {
        font-size: 2rem;
        color: var(--green);
        padding-bottom: 0.5rem;
    }

    header img {
        display: block;
        width: 3rem;
        height: 3rem;
        margin-right: 1rem;
    }

    main {
        max-width: 60rem;
        margin: 0 auto;
        padding: 0 1rem 2rem;
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
    }
</style>
