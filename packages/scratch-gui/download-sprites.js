const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');

// 读取 sprites.json 文件
const spritesData = JSON.parse(fs.readFileSync('./src/lib/libraries/sprites.json', 'utf8'));

// 创建下载目录
const downloadDir = './downloaded-sprites';
if (!fs.existsSync(downloadDir)) {
    fs.mkdirSync(downloadDir, {recursive: true});
}

// 收集所有唯一的 assetId
const assetIds = new Set();

const extractAssetIds = obj => {
    if (typeof obj === 'object' && obj !== null) {
        if (obj.assetId) {
            assetIds.add(obj.assetId);
        }
        for (const key in obj) {
            extractAssetIds(obj[key]);
        }
    } else if (Array.isArray(obj)) {
        obj.forEach(extractAssetIds);
    }
};

// 提取所有 assetId
extractAssetIds(spritesData);

console.log(`找到 ${assetIds.size} 个唯一的资源 ID`);

// 下载函数 https://cdn.assets.scratch.mit.edu/internalapi/asset/a09376e1eacf17be3c9fbd268674b9f7.svg/get/
const downloadAsset = assetId => new Promise((resolve, reject) => {
    const url = `https://cdn.assets.scratch.mit.edu/internalapi/asset/${assetId}.svg/get/`;
    const filePath = path.join(downloadDir, `${assetId}.svg`);
    
    // 如果文件已存在，跳过下载
    if (fs.existsSync(filePath)) {
        console.log(`跳过已存在的文件: ${assetId}.svg`);
        resolve();
        return;
    }

    const protocol = url.startsWith('https:') ? https : http;
    
    protocol.get(url, response => {
        if (response.statusCode === 200) {
            const fileStream = fs.createWriteStream(filePath);
            response.pipe(fileStream);
            
            fileStream.on('finish', () => {
                fileStream.close();
                console.log(`下载完成: ${assetId}.svg`);
                resolve();
            });
            
            fileStream.on('error', err => {
                fs.unlink(filePath, () => {}); // 删除不完整的文件
                reject(err);
            });
        } else {
            console.error(`下载失败 ${assetId}.svg: HTTP ${response.statusCode}`);
            reject(new Error(`HTTP ${response.statusCode}`));
        }
    }).on('error', err => {
        console.error(`下载错误 ${assetId}.svg:`, err.message);
        reject(err);
    });
});

// 批量下载函数（限制并发数）
const downloadAllAssets = async (assetIdList, concurrency = 5) => {
    const assetArray = Array.from(assetIdList);
    const results = [];
    
    for (let i = 0; i < assetArray.length; i += concurrency) {
        const batch = assetArray.slice(i, i + concurrency);
        const promises = batch.map(assetId =>
            downloadAsset(assetId).catch(err => {
                console.error(`资源 ${assetId} 下载失败:`, err.message);
                return {error: err, assetId};
            })
        );
        
        const batchResults = await Promise.all(promises);
        results.push(...batchResults);
        
        console.log(`批次 ${Math.floor(i / concurrency) + 1}/${Math.ceil(assetArray.length / concurrency)} 完成`);
    }
    
    return results;
};

// 创建资源映射文件
const createAssetMapping = () => {
    const mapping = {};
    
    const processSprite = sprite => {
        if (sprite.costumes) {
            sprite.costumes.forEach(costume => {
                if (costume.assetId) {
                    mapping[costume.assetId] = {
                        spriteName: sprite.name,
                        costumeName: costume.name,
                        fileName: costume.md5ext || `${costume.assetId}.svg`,
                        dataFormat: costume.dataFormat,
                        rotationCenterX: costume.rotationCenterX,
                        rotationCenterY: costume.rotationCenterY
                    };
                }
            });
        }
        
        if (sprite.sounds) {
            sprite.sounds.forEach(sound => {
                if (sound.assetId) {
                    mapping[sound.assetId] = {
                        spriteName: sprite.name,
                        soundName: sound.name,
                        fileName: sound.md5ext || `${sound.assetId}.wav`,
                        dataFormat: sound.dataFormat,
                        duration: sound.duration
                    };
                }
            });
        }
    };
    
    spritesData.forEach(processSprite);
    
    const mappingPath = path.join(downloadDir, 'asset-mapping.json');
    fs.writeFileSync(mappingPath, JSON.stringify(mapping, null, 2), 'utf8');
    console.log(`资源映射文件已创建: ${mappingPath}`);
};

// 主函数
const main = async () => {
    console.log('开始下载 Scratch 精灵资源...');
    console.log(`目标目录: ${path.resolve(downloadDir)}`);
    
    try {
        // 创建资源映射
        createAssetMapping();
        
        // 下载所有资源
        const results = await downloadAllAssets(assetIds, 5);
        
        const errors = results.filter(result => result && result.error);
        const successCount = results.length - errors.length;
        
        console.log('\n下载完成!');
        console.log(`成功下载: ${successCount} 个文件`);
        console.log(`失败: ${errors.length} 个文件`);
        
        if (errors.length > 0) {
            console.log('\n失败的文件:');
            errors.forEach(error => {
                console.log(`- ${error.assetId}: ${error.error.message}`);
            });
        }
        
        console.log(`\n所有文件已保存到: ${path.resolve(downloadDir)}`);
        
    } catch (error) {
        console.error('下载过程中发生错误:', error);
    }
};

// 运行主函数
main();
