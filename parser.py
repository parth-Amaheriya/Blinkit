import json
from models import Product,PriceItem,Media
import gzip
import re
 


def extract_price(price_text):
    if not price_text:
        return ""
    
    match=re.search(r'₹[\d,]+', price_text)
    if match:
        return match.group(0)
    return price_text

def parse_file(filename):
    try:
        with gzip.open(filename, 'rt', encoding='utf-8') as f:
            raw=json.load(f)

        response=raw.get('response', {})
        snippets=response.get("snippets", [])
        
        product_name=""
        brand=""
        prices=[]
        images=[]
        videos=[]
        product_details={}
        
        
        found_multiple_prices=False
        
        for i, snippet in enumerate(snippets):
            data=snippet.get("data", {})
            widget_type=snippet.get("widget_type", "")
            
            if widget_type == "horizontal_list" and data.get("horizontal_item_list"):
                item_list=data.get("horizontal_item_list", [])
                first_item={}
                for item in item_list:
                    if item:
                        first_item=item
                        break
                item_data=first_item.get("data", first_item)
                    
                if item_data.get("title") and not item_data.get("name"):
                    found_multiple_prices=True
                    
                    if first_item.get("tracking"):
                        click_map=first_item["tracking"].get("click_map", {})
                        if click_map:
                            product_name=click_map.get("name", "")
                            brand=click_map.get("brand", "")
                    
                    for item in item_list:
                        item_data=item.get("data", item)
                        
                        title_text=item_data.get("title", {}).get("text", "") if isinstance(item_data.get("title"), dict) else ""
                        subtitle_text=item_data.get("subtitle", {}).get("text", "") if isinstance(item_data.get("subtitle"), dict) else ""
                        subtitle2_text=item_data.get("subtitle2", {}).get("text", "") if isinstance(item_data.get("subtitle2"), dict) else ""
                        
                        if title_text and subtitle_text:
                            try:
                                if subtitle2_text:
                                    price_item=PriceItem(
                                        weight=title_text,
                                        original=subtitle2_text,
                                        discounted=subtitle_text,
                                    )
                                else:
                                    price_item=PriceItem(
                                        weight=title_text,
                                        original=subtitle_text,
                                        discounted=subtitle_text,
                                    )
                                prices.append(price_item)
                            except ValueError as e:
                                print(f"Invalid price data: {e}")
        
        
        if not found_multiple_prices:
            for i, snippet in enumerate(snippets):
                data=snippet.get("data", {})
                widget_type=snippet.get("widget_type", "")
                
                if widget_type == "product_atc_strip":
                    variant_text=data.get("variant", {}).get("text", "") if isinstance(data.get("variant"), dict) else ""
                    
                    normal_price_text=data.get("normal_price", {}).get("text", "") if isinstance(data.get("normal_price"), dict) else ""
                    
                    mrp_text=data.get("mrp", {}).get("text", "") if isinstance(data.get("mrp"), dict) else ""
                    
                    if not product_name:
                        atc_actions=data.get("atc_actions_v2", {})
                        if atc_actions:
                            for action_list in atc_actions.values():
                                if action_list and action_list[0]:
                                    action=action_list[0]
                                    if action.get("add_to_cart"):
                                        cart_item=action["add_to_cart"].get("cart_item", {})
                                        if cart_item:
                                            product_name=cart_item.get("product_name", "")
                                            brand=cart_item.get("brand", "")
                                            break
                    
                    if not product_name:
                        rfc_actions=data.get("rfc_actions_v2", {})
                        if rfc_actions:
                            for action_list in rfc_actions.values():
                                if action_list and action_list[0]:
                                    action=action_list[0]
                                    if action.get("remove_from_cart"):
                                        cart_item=action["remove_from_cart"].get("cart_item", {})
                                        if cart_item:
                                            product_name=cart_item.get("product_name", "")
                                            brand=cart_item.get("brand", "")
                                            break
                    
                    if variant_text and normal_price_text:
                        try:
                            original_price=extract_price(mrp_text) if mrp_text else normal_price_text
                            
                            price_item=PriceItem(
                                weight=variant_text,
                                original=original_price,
                                discounted=normal_price_text,
                            )
                            prices.append(price_item)
                        except ValueError as e:
                            print(f"Invalid price data: {e}")
                    
                    break  
        
        for snippet in snippets:
            data=snippet.get("data", {})
            
            if data.get("itemList"):
                item_list=data.get("itemList", [])
                for item in item_list:
                    media_content=item.get("data", {}).get("media_content", {})
                    if media_content.get("media_type") == "image":
                        img_url=media_content.get("image", {}).get("url", "")
                        if img_url and img_url not in images:
                            images.append(img_url)
                    
                    elif media_content.get("media_type") == "video":
                        video_url=media_content.get("video", {}).get("url", "")
                        if video_url and video_url not in videos:
                            videos.append(video_url)
        
        try:
            snippet_list_updater_data=response.get("snippet_list_updater_data", {})
            expand_attributes=snippet_list_updater_data.get("expand_attributes", {})
            payload=expand_attributes.get("payload", {})
            snippets_to_add=payload.get("snippets_to_add", [])
            
            for snippet in snippets_to_add:
                snippet_data=snippet.get("data", {})
                attr_name=snippet_data.get("title", {}).get("text", "").strip()
                attr_value=snippet_data.get("subtitle", {}).get("text", "").strip()
                
                if attr_name and attr_value:
                    product_details[attr_name]=attr_value
        except Exception as e:
            print(f"Could not extract product details: {e}")
        
        media=Media(
            image=images,
            video=videos
        )
    
        if product_name and prices:
            
            final_data=Product(
                product_name=product_name,
                brand=brand,
                price=prices,
                media=media,
                product_details=product_details
            )
            return final_data
        else:
            print("Error: Could not extract product name or prices")
            return None
            
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return None