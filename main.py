from importlib import import_module
Wiki = import_module('TFWiki-scripts.wikitools.wiki').Wiki
Page = import_module('TFWiki-scripts.wikitools.page').Page

verbose = False

def main(w):
  expeditions = Page(w, 'User:Darkid/Potential_expeditions')

  contents = expeditions.get_wiki_text()

  if verbose:
    print(contents)

  # Do stuff

  expeditions.edit(contents, bot=True, summary='Automated update by darkid\'s bot')

if __name__ == '__main__':
  verbose = True
  w = Wiki('https://geohashing.site/api.php')
  main(w)
