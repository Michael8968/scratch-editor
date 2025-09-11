#!/usr/bin/env python3
"""
Scratch 精灵资源下载脚本
从 sprites.json 文件中提取所有 assetId，并使用 CDN URL 下载到本地
"""

import json
import os
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Set, Dict, Any

def load_sprites_data(file_path: str) -> list:
    """加载 sprites.json 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def download_asset(asset_id: str, file_name: str, data_format: str, download_dir: Path, session: requests.Session) -> Dict[str, Any]:
    """下载单个资源"""
    url = f"https://cdn.assets.scratch.mit.edu/internalapi/asset/{asset_id}.{data_format}/get/"
    file_path = download_dir / file_name
    
    result = {
        'asset_id': asset_id,
        'file_name': file_name,
        'data_format': data_format,
        'success': False,
        'error': None,
        'file_path': str(file_path)
    }
    
    # 如果文件已存在，跳过下载
    if file_path.exists():
        print(f"跳过已存在的文件: {file_name}")
        result['success'] = True
        return result
    
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        print(f"下载完成: {file_name}")
        result['success'] = True
        
    except requests.exceptions.RequestException as e:
        error_msg = f"下载失败 {file_name}: {str(e)}"
        print(error_msg)
        result['error'] = error_msg
        
        # 删除不完整的文件
        if file_path.exists():
            file_path.unlink()
    
    return result

def create_asset_mapping(sprites_data: list, backdrops_data: list, costumes_data: list, sounds_data: list, download_dir: Path) -> Dict[str, Dict[str, Any]]:
    """创建资源映射文件并返回资源信息"""
    mapping = {}
    assets_to_download = []
    
    def process_sprite(sprite: Dict[str, Any]) -> None:
        sprite_name = sprite.get('name', 'unknown')
        
        # 处理服装
        if 'costumes' in sprite:
            for costume in sprite['costumes']:
                if 'assetId' in costume:
                    asset_id = costume['assetId']
                    file_name = costume.get('md5ext', f"{asset_id}.svg")
                    data_format = costume.get('dataFormat', 'svg')
                    
                    mapping[asset_id] = {
                        'spriteName': sprite_name,
                        'costumeName': costume.get('name', 'unknown'),
                        'fileName': file_name,
                        'dataFormat': data_format,
                        'rotationCenterX': costume.get('rotationCenterX'),
                        'rotationCenterY': costume.get('rotationCenterY')
                    }
                    
                    assets_to_download.append({
                        'asset_id': asset_id,
                        'file_name': file_name,
                        'data_format': data_format
                    })
        
        # 处理声音
        if 'sounds' in sprite:
            for sound in sprite['sounds']:
                if 'assetId' in sound:
                    asset_id = sound['assetId']
                    file_name = sound.get('md5ext', f"{asset_id}.wav")
                    data_format = sound.get('dataFormat', 'wav')
                    
                    mapping[asset_id] = {
                        'spriteName': sprite_name,
                        'soundName': sound.get('name', 'unknown'),
                        'fileName': file_name,
                        'dataFormat': data_format,
                        'duration': sound.get('duration')
                    }
                    
                    assets_to_download.append({
                        'asset_id': asset_id,
                        'file_name': file_name,
                        'data_format': data_format
                    })
    
    def process_backdrop(backdrop: Dict[str, Any]) -> None:
        backdrop_name = backdrop.get('name', 'unknown')
        if 'assetId' in backdrop:
            asset_id = backdrop['assetId']
            file_name = backdrop.get('md5ext', f"{asset_id}.png")
            data_format = backdrop.get('dataFormat', 'png')
            
            mapping[asset_id] = {
                'backdropName': backdrop_name,
                'fileName': file_name,
                'dataFormat': data_format,
                'rotationCenterX': backdrop.get('rotationCenterX'),
                'rotationCenterY': backdrop.get('rotationCenterY'),
                'bitmapResolution': backdrop.get('bitmapResolution')
            }
            
            assets_to_download.append({
                'asset_id': asset_id,
                'file_name': file_name,
                'data_format': data_format
            })
    
    def process_costume(costume: Dict[str, Any]) -> None:
        costume_name = costume.get('name', 'unknown')
        if 'assetId' in costume:
            asset_id = costume['assetId']
            file_name = costume.get('md5ext', f"{asset_id}.svg")
            data_format = costume.get('dataFormat', 'svg')
            
            mapping[asset_id] = {
                'costumeName': costume_name,
                'fileName': file_name,
                'dataFormat': data_format,
                'rotationCenterX': costume.get('rotationCenterX'),
                'rotationCenterY': costume.get('rotationCenterY'),
                'bitmapResolution': costume.get('bitmapResolution')
            }
            
            assets_to_download.append({
                'asset_id': asset_id,
                'file_name': file_name,
                'data_format': data_format
            })
    
    def process_sound(sound: Dict[str, Any]) -> None:
        sound_name = sound.get('name', 'unknown')
        if 'assetId' in sound:
            asset_id = sound['assetId']
            file_name = sound.get('md5ext', f"{asset_id}.wav")
            data_format = sound.get('dataFormat', 'wav')
            
            mapping[asset_id] = {
                'soundName': sound_name,
                'fileName': file_name,
                'dataFormat': data_format,
                'duration': sound.get('duration')
            }
            
            assets_to_download.append({
                'asset_id': asset_id,
                'file_name': file_name,
                'data_format': data_format
            })
    
    # 处理精灵数据
    for sprite in sprites_data:
        process_sprite(sprite)
    
    # 处理背景数据
    for backdrop in backdrops_data:
        process_backdrop(backdrop)
    
    # 处理服装数据
    for costume in costumes_data:
        process_costume(costume)
    
    # 处理声音数据
    for sound in sounds_data:
        process_sound(sound)
    
    mapping_path = download_dir / 'asset-mapping.json'
    with open(mapping_path, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)
    
    print(f"资源映射文件已创建: {mapping_path}")
    return assets_to_download

def download_all_assets(assets_to_download: list, download_dir: Path, max_workers: int = 5) -> list:
    """批量下载所有资源"""
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        with requests.Session() as session:
            # 设置请求头
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            # 提交所有下载任务
            future_to_asset = {
                executor.submit(
                    download_asset, 
                    asset['asset_id'], 
                    asset['file_name'], 
                    asset['data_format'], 
                    download_dir, 
                    session
                ): asset
                for asset in assets_to_download
            }
            
            # 收集结果
            for future in as_completed(future_to_asset):
                asset = future_to_asset[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"处理 {asset['file_name']} 时发生异常: {str(e)}")
                    results.append({
                        'asset_id': asset['asset_id'],
                        'file_name': asset['file_name'],
                        'data_format': asset['data_format'],
                        'success': False,
                        'error': str(e),
                        'file_path': None
                    })
    
    return results

def main():
    """主函数"""
    print("开始下载 Scratch 精灵资源...")
    
    # 文件路径
    sprites_file = Path('./src/lib/libraries/sprites.json')
    download_dir = Path('./downloaded-sprites')
    
    # 检查 sprites.json 文件是否存在
    if not sprites_file.exists():
        print(f"错误: 找不到文件 {sprites_file}")
        return
    
    # 创建下载目录
    download_dir.mkdir(exist_ok=True)
    print(f"目标目录: {download_dir.absolute()}")
    
    try:
        # 加载所有数据文件
        print("加载资源文件...")
        sprites_data = load_sprites_data(sprites_file)
        backdrops_data = load_sprites_data(Path('./src/lib/libraries/backdrops.json'))
        costumes_data = load_sprites_data(Path('./src/lib/libraries/costumes.json'))
        sounds_data = load_sprites_data(Path('./src/lib/libraries/sounds.json'))
        
        print(f"加载完成:")
        print(f"  - 精灵: {len(sprites_data)} 个")
        print(f"  - 背景: {len(backdrops_data)} 个")
        print(f"  - 服装: {len(costumes_data)} 个")
        print(f"  - 声音: {len(sounds_data)} 个")
        
        # 创建资源映射并获取要下载的资源列表
        print("分析资源信息...")
        assets_to_download = create_asset_mapping(sprites_data, backdrops_data, costumes_data, sounds_data, download_dir)
        print(f"找到 {len(assets_to_download)} 个资源需要下载")
        
        # 统计不同格式的文件数量
        format_counts = {}
        for asset in assets_to_download:
            format_type = asset['data_format']
            format_counts[format_type] = format_counts.get(format_type, 0) + 1
        
        print("文件格式统计:")
        for format_type, count in format_counts.items():
            print(f"  {format_type}: {count} 个文件")
        
        # 下载所有资源
        print("开始下载资源...")
        start_time = time.time()
        results = download_all_assets(assets_to_download, download_dir, max_workers=5)
        end_time = time.time()
        
        # 统计结果
        success_count = sum(1 for r in results if r['success'])
        error_count = len(results) - success_count
        
        print(f"\n下载完成!")
        print(f"耗时: {end_time - start_time:.2f} 秒")
        print(f"成功下载: {success_count} 个文件")
        print(f"失败: {error_count} 个文件")
        
        if error_count > 0:
            print("\n失败的文件:")
            for result in results:
                if not result['success']:
                    print(f"- {result['file_name']}: {result['error']}")
        
        print(f"\n所有文件已保存到: {download_dir.absolute()}")
        
    except Exception as e:
        print(f"下载过程中发生错误: {str(e)}")

if __name__ == "__main__":
    main()

