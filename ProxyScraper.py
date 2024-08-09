import json
import threading
import re
import cloudscraper

def load_config():
    with open('config.json', 'r') as file:
        return json.load(file)

def load_links(file_name):
    with open(file_name, 'r') as file:
        return file.read().splitlines()

def save_proxies(file_name, proxies):
    with open(file_name, 'w') as file:
        for proxy in proxies:
            file.write(f"{proxy}\n")

def remove_duplicates(proxies):
    seen = set()
    unique_proxies = []
    for proxy in proxies:
        if proxy not in seen:
            unique_proxies.append(proxy)
            seen.add(proxy)
    duplicates_removed = len(proxies) - len(unique_proxies)
    print(f"Removed {duplicates_removed} duplicate proxies. {len(unique_proxies)} proxies remain.")
    return unique_proxies

def remove_same_ip(proxies):
    seen_ips = set()
    unique_proxies = []
    for proxy in proxies:
        ip = proxy.split(':')[0]
        if ip not in seen_ips:
            unique_proxies.append(proxy)
            seen_ips.add(ip)
    same_ip_removed = len(proxies) - len(unique_proxies)
    print(f"Removed {same_ip_removed} proxies with the same IP. {len(unique_proxies)} proxies remain.")
    return unique_proxies

def remove_ports(proxies):
    return [re.sub(r':\d+', '', proxy) for proxy in proxies]

def remove_protocols(proxies):
    return [re.sub(r'^(socks4://|http://|socks5://|https://)', '', proxy) for proxy in proxies]

def clean_ip_port(proxies):
    return [re.sub(r'.*?(\d+\.\d+\.\d+\.\d+:\d+).*', r'\1', proxy) for proxy in proxies]

def remove_local(proxies):
    local_ip_patterns = [
        re.compile(r'^127\.\d+\.\d+\.\d+'),
        re.compile(r'^10\.\d+\.\d+\.\d+'),
        re.compile(r'^172\.(1[6-9]|2[0-9]|3[0-1])\.\d+\.\d+'),
        re.compile(r'^192\.168\.\d+\.\d+')
    ]
    filtered_proxies = []
    for proxy in proxies:
        ip = proxy.split(':')[0]
        if not any(pattern.match(ip) for pattern in local_ip_patterns):
            filtered_proxies.append(proxy)
    local_removed = len(proxies) - len(filtered_proxies)
    print(f"Removed {local_removed} local proxies. {len(filtered_proxies)} proxies remain.")
    return filtered_proxies

def fetch_proxies_from_link(link, result):
    scraper = cloudscraper.create_scraper()
    try:
        response = scraper.get(link)
        status_code = response.status_code
        proxies = response.text.splitlines()
        print(f"Fetched from {link} with status code {status_code}. Proxies found: {len(proxies)}")
        result.extend(proxies)
    except cloudscraper.exceptions.CloudflareChallengeError as e:
        print(f"Error fetching proxies from {link}: {e}")

def scrape_proxies(input_file_name, config):
    links = load_links(input_file_name)
    proxies = []
    thread_list = []
    result = []

    for link in links:
        thread = threading.Thread(target=fetch_proxies_from_link, args=(link, result))
        thread_list.append(thread)
        thread.start()

    for thread in thread_list:
        thread.join()

    proxies.extend(result)

    if config['previous_proxies']:
        previous_proxies = load_links(config['output_file_name'])
        proxies.extend(previous_proxies)

    if config['duplicates_remover']:
        proxies = remove_duplicates(proxies)

    if config['remove_same_ip']:
        proxies = remove_same_ip(proxies)

    if config['port_remover']:
        proxies = remove_ports(proxies)

    if config['protocol_remover']:
        proxies = remove_protocols(proxies)

    if config['clean_ip_port']:
        proxies = clean_ip_port(proxies)

    if config['remove_local']:
        proxies = remove_local(proxies)

    return proxies

def main():
    config = load_config()
    input_file_name = config['input_file_name']
    output_file_name = config['output_file_name']

    proxies = scrape_proxies(input_file_name, config)
    save_proxies(output_file_name, proxies)

if __name__ == "__main__":
    main()
