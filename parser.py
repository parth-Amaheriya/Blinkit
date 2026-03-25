import json
from models import Product, PriceItem, Media
import gzip
import re


def extract_price_from_text(price_text):
    if not price_text:
        return ""
    match=re.search(r'₹[\d,]+', price_text)
    return match.group(0) if match else price_text


def parse_file(filename):
    try:
        with gzip.open(filename, 'rt', encoding='utf-8') as f:
            raw=json.load(f)

        response=raw.get('response', {})
        snippets=response.get("snippets", [])

        product_name=""
        brand=""
        prices=[]
        product_details={}

        images, videos=[], []
        seen_images, seen_videos=set(), set()

        found_multiple_prices=False

        for snippet in snippets:
            snippet=snippet or {}  

            data=snippet.get("data") or {}
            widget_type=snippet.get("widget_type") or ""

            # multiple prices
            if widget_type == "horizontal_list":
                item_list=data.get("horizontal_item_list") or []

                if item_list:
                    first_item=item_list[0] or {}
                    item_data=first_item.get("data") or first_item or {}

                    if item_data.get("title") and not item_data.get("name"):
                        found_multiple_prices=True

                        click_map=(first_item.get("tracking") or {}).get("click_map") or {}
                        product_name=click_map.get("name", "")
                        brand=click_map.get("brand", "")

                        for idx, item in enumerate(item_list):
                            item=item or {}
                            item_data=item.get("data") or item or {}

                            title=item_data.get("title") or {}
                            subtitle=item_data.get("subtitle") or {}
                            subtitle2=item_data.get("subtitle2") or {}

                            title_text=title.get("text", "") if isinstance(title, dict) else ""
                            subtitle_text=subtitle.get("text", "") if isinstance(subtitle, dict) else ""
                            subtitle2_text=subtitle2.get("text", "") if isinstance(subtitle2, dict) else ""

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
                    
            #  single price
            elif not found_multiple_prices and widget_type == "product_atc_strip":
            
                variant=data.get("variant") or {}
                normal_price=data.get("normal_price") or {}
                mrp=data.get("mrp") or {}

                variant_text=variant.get("text", "") if isinstance(variant, dict) else ""
                normal_price_text=normal_price.get("text", "") if isinstance(normal_price, dict) else ""
                mrp_text=mrp.get("text", "") if isinstance(mrp, dict) else ""

                if not product_name:
                    for action_group in ("atc_actions_v2", "rfc_actions_v2"):
                        for action_list in (data.get(action_group) or {}).values():
                            if action_list:
                                action=action_list[0] or {}
                                cart=action.get("add_to_cart") or action.get("remove_from_cart")
                                if cart:
                                    cart_item=cart.get("cart_item") or {}
                                    product_name=cart_item.get("product_name", "")
                                    brand=cart_item.get("brand", "")
                                    break
                                
                if variant_text and normal_price_text:
                    try:
                        original_price=extract_price_from_text(mrp_text) if mrp_text else normal_price_text

                        prices.append(PriceItem(
                            weight=variant_text,
                            original=original_price,
                            discounted=normal_price_text,
                            is_selected=True
                        ))
                    except ValueError as e:
                        print(f"Invalid price data: {e}")

                break
            
            # media
            for item in data.get("itemList") or []:
                item=item or {}
                media=(item.get("data") or {}).get("media_content") or {}

                media_type=media.get("media_type")

                if media_type == "image":
                    url=(media.get("image") or {}).get("url")
                    if url and url not in seen_images:
                        seen_images.add(url)
                        images.append(url)

                elif media_type == "video":
                    url=(media.get("video") or {}).get("url")
                    if url and url not in seen_videos:
                        seen_videos.add(url)
                        videos.append(url)

        # product deatils
        try:
            payload=(
                response.get("snippet_list_updater_data", {})
                .get("expand_attributes", {})
                .get("payload", {})
            )

            for snippet in payload.get("snippets_to_add", []):
                data=snippet.get("data", {})
                key=data.get("title", {}).get("text", "").strip()
                value=data.get("subtitle", {}).get("text", "").strip()

                if key and value:
                    product_details[key]=value

        except Exception as e:
            print(f"Could not extract product details: {e}")

        media=Media(image=images, video=videos)

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