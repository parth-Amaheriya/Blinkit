

import json
from models import Product, PriceItem, Media
import gzip
import re


def extract_price_from_text(price_text):
    if not price_text:
        return ""
    matches = re.findall(r'₹[\d,]+', price_text)
    return matches[0] if matches else price_text


def parse_file(filename):
    try:
        with gzip.open(filename, 'rt', encoding='utf-8') as f:
            raw = json.load(f)

        response = raw.get('response', {})
        snippets = response.get("snippets", [])

        product_name = ""
        brand = ""
        prices = []
        product_details = {}

        images, videos = [], []
        seen_images, seen_videos = set(), set()

        found_multiple_prices = False

        for snippet in snippets:
            data = snippet.get("data", {})
            widget_type = snippet.get("widget_type", "")

            # MULTIPLE PRICES 
            if widget_type == "horizontal_list":
                item_list = data.get("horizontal_item_list", [])

                if item_list:
                    # Detect multiple price structure
                    for item in item_list:
                        item_data = item.get("data",{})

                        if item_data.get("title","") and not item_data.get("name",""):
                            found_multiple_prices = True
                            break

                    if found_multiple_prices:
                        # Extract product 
                        for item in item_list:
                            click_map = item.get("tracking",{}).get("click_map",{})

                            if click_map.get("name",""):
                                product_name = click_map.get("name", "")
                                brand = click_map.get("brand", "")
                                break

                        # Extract price variants
                        for idx, item in enumerate(item_list):
                            item_data = item.get("data",{}) 

                            title = item_data.get("title",{}) 
                            subtitle = item_data.get("subtitle",{})
                            subtitle2 = item_data.get("subtitle2",{}) 

                            title_text = title.get("text", "")
                            subtitle_text = subtitle.get("text", "") 
                            subtitle2_text = subtitle2.get("text", "") 

                            if title_text and subtitle_text:
                                try:
                                    prices.append(PriceItem(
                                        weight=title_text,
                                        original=subtitle2_text or subtitle_text,
                                        discounted=subtitle_text,
                                        is_selected=(idx == 0)
                                    ))
                                except ValueError as e:
                                    print(f"Invalid price data: {e}")

                        continue

            # SINGLE PRICE
            elif not found_multiple_prices and widget_type == "product_atc_strip":

                variant = data.get("variant",{})
                normal_price = data.get("normal_price",{})
                mrp = data.get("mrp",{})

                variant_text = variant.get("text", "") 
                normal_price_text = normal_price.get("text", "") 
                mrp_text = mrp.get("text", "")

                if not product_name:
                    for action_group in ("atc_actions_v2", "rfc_actions_v2"):
                        for action_list in (data.get(action_group,{})).values():
                            if action_list:
                                action = action_list[0] or {}
                                cart = action.get("add_to_cart",{}) or action.get("remove_from_cart",{})
                                if cart:
                                    cart_item = cart.get("cart_item",{})
                                    product_name = cart_item.get("product_name", "")
                                    brand = cart_item.get("brand", "")
                                    break

                if variant_text and normal_price_text:
                    try:
                        original_price = extract_price_from_text(mrp_text) if mrp_text else normal_price_text

                        prices.append(PriceItem(
                            weight=variant_text,
                            original=original_price,
                            discounted=normal_price_text,
                            is_selected=True
                        ))
                    except ValueError as e:
                        print(f"Invalid price data: {e}")

                break

            # MEDIA
            for item in data.get("itemList",[]):
                media = item.get("data",{}).get("media_content",{})

                media_type = media.get("media_type","")

                if media_type == "image":
                    url = media.get("image",{}).get("url")
                    if url and url not in seen_images:
                        seen_images.add(url)
                        images.append(url)

                elif media_type == "video":
                    url = media.get("video",{}).get("url")
                    if url and url not in seen_videos:
                        seen_videos.add(url)
                        videos.append(url)

        # PRODUCT DETAILS
        try:
            payload = (
                response.get("snippet_list_updater_data", {})
                .get("expand_attributes", {})
                .get("payload", {})
            )

            for snippet in payload.get("snippets_to_add", []):
                data = snippet.get("data", {})
                key = data.get("title", {}).get("text", "").strip()
                value = data.get("subtitle", {}).get("text", "").strip()

                if key and value:
                    product_details[key] = value

        except Exception as e:
            print(f"Could not extract product details: {e}")

        media = Media(image=images, video=videos)

        if product_name and prices:
            return Product(
                product_name=product_name,
                brand=brand,
                price=prices,
                media=media,
                product_details=product_details
            )

        print("Error: Could not extract product name or prices")
        return None

    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return None