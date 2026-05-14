<%*
// Reveal a location to players.
// Run this on any gm_secrets location file to promote it to public
// and stamp the reveal date. No content is inserted — frontmatter only.
const file = tp.file.find_tfile(tp.file.path(true));
await app.fileManager.processFrontMatter(file, (fm) => {
  fm['visibility'] = 'public';
  fm['revealed'] = tp.date.now('YYYY-MM-DD');
  fm['last_updated'] = tp.date.now('YYYY-MM-DD');
});
tR = '';
-%>
