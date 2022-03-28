from models import Extension, Manga


def search(ext_active: Extension, query: str) -> Manga:
    """Retrieves manga from searching

    Args:
        ext_active (Extension): Subclass of Extension class the site extension creates
        query (str): Query string to search for manga

    Returns:
        Manga: models.Manga object with only id and title attributes populated
    """

    manga = None
    reinput = True
    search_page = 1
    page_index_in = -1

    while manga == None:
        # first retrieves list of manga from search query
        search_res = ext_active.search(query, search_page)

        if len(search_res.manga_list) == 0:
            print("There are 0 results for your search query. Exiting...")
            return

        print(f"Search results for '{query}' page {search_page}:")

        for i in range(search_res.length):
            print(f"{i+1}. {search_res.manga_list[i].title}")

        reinput = True

        # keep asking until a manga selection is made, flagged by reinput
        while reinput:
            max_num = len(search_res.manga_list)
            query_str = f"Which manga do you wish to download (1-{max_num}, < or > to move search page, q to quit): "
            page_index_in = (input(query_str) or "q").strip()

            if (page_index_in == "q"):
                return

            print("")

            # if user wants to navigate pages
            if page_index_in in ["<", ">"]:
                # decrementing page below 1
                if search_page == 1 and page_index_in == "<":
                    page_index_in = -1
                    print("You can't go to a previous page")
                    continue

                # incrementing page when last page is reached
                elif search_res.last_page and page_index_in == ">":
                    page_index_in = -1
                    print("You can't go to a next page")
                    continue

                # increment/decrement as per usual
                else:
                    search_page += -1 if page_index_in == "<" else 1
                    reinput = False

                page_index_in = -1

            # if user input was an integer
            elif page_index_in.isdigit():
                page_index_in = int(page_index_in) - 1

                if page_index_in < 0 or page_index_in >= search_res.length:
                    print("Index out of range of search results")
                else:
                    reinput = False

            # input was none of the above specified
            else:
                print("Invalid input")

        # only choose manga if valid index is input via user
        if page_index_in >= 0 and page_index_in < len(search_res.manga_list):
            manga = search_res.manga_list[page_index_in]
            print(f"You chose: '{manga.title}'")

    return manga
# end_search
