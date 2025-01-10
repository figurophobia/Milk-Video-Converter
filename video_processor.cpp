#include <opencv2/opencv.hpp>
#include <iostream>
#include <fstream>
#include <filesystem>
#include <thread>
#include <vector>
#include <random>
#include <iomanip>
#include <sstream>

namespace fs = std::filesystem;

int getVideoFPS(const std::string& videoPath) {
    cv::VideoCapture cap(videoPath);
    if (!cap.isOpened()) {
        throw std::runtime_error("Error opening video file");
    }
    return static_cast<int>(cap.get(cv::CAP_PROP_FPS));
}

void extractFrames(const std::string& videoPath, const std::string& outputFolder, int fps) {
    cv::VideoCapture cap(videoPath);
    if (!cap.isOpened()) {
        throw std::runtime_error("Error opening video file");
    }

    double frameRate = cap.get(cv::CAP_PROP_FPS);
    int frameStep = static_cast<int>(frameRate / fps);
    int extractedFrameCount = 0;

    fs::create_directory(outputFolder);

    cv::Mat frame;
    while (cap.read(frame)) {
        if (extractedFrameCount % frameStep == 0) {
            std::ostringstream filename;
            filename << outputFolder << "/frame" << std::setw(6) << std::setfill('0') << extractedFrameCount << ".jpg";
            cv::imwrite(filename.str(), frame);
        }
        extractedFrameCount++;
    }
}

bool probably(double prob) {
    static std::random_device rd;
    static std::mt19937 gen(rd());
    std::bernoulli_distribution d(prob);
    return d(gen);
}

cv::Mat applyFilter(const cv::Mat& image, bool compression, bool effect, int milkType, int quality, const std::string& framePath) {
    int punt = effect ? 70 : 100;

    cv::Mat imag;
    if (image.channels() == 3) {
        cv::cvtColor(image, imag, cv::COLOR_BGR2RGB);
    } else {
        imag = image.clone();
    }

    if (compression) {
        std::string outputFolder = "filtered_frames";
        fs::create_directory(outputFolder);
        std::string outputPath = outputFolder + "/" + fs::path(framePath).stem().string() + ".jpg";
        std::vector<int> compression_params = { cv::IMWRITE_JPEG_QUALITY, 100 - quality };
        cv::imwrite(outputPath, imag, compression_params);
        imag = cv::imread(outputPath);
    }

    int width = imag.cols;
    int height = imag.rows;

    for (int x = 0; x < width; ++x) {
        for (int y = 0; y < height; ++y) {
            cv::Vec3b pixelRGB = imag.at<cv::Vec3b>(y, x);
            int R = pixelRGB[0];
            int G = pixelRGB[1];
            int B = pixelRGB[2];
            int brightness = (R + G + B) / 3;
            cv::Vec4b new_pixel(0, 0, 0, 255);  // Default black

            if (milkType == 1) {
                if (brightness <= 25) {
                    new_pixel = cv::Vec4b(0, 0, 0, 255);
                } else if (brightness <= 70) {
                    new_pixel = (probably(punt / 100.0)) ? cv::Vec4b(0, 0, 0, 255) : cv::Vec4b(102, 0, 31, 255);
                } else if (brightness < 120) {
                    new_pixel = (probably(punt / 100.0)) ? cv::Vec4b(102, 0, 31, 255) : cv::Vec4b(0, 0, 0, 255);
                } else if (brightness < 200) {
                    new_pixel = cv::Vec4b(102, 0, 31, 255);
                } else if (brightness < 230) {
                    new_pixel = (probably(punt / 100.0)) ? cv::Vec4b(137, 0, 146, 255) : cv::Vec4b(102, 0, 31, 255);
                } else {
                    new_pixel = cv::Vec4b(137, 0, 146, 255);
                }
            } else {
                if (brightness <= 25) {
                    new_pixel = cv::Vec4b(0, 0, 0, 255);
                } else if (brightness <= 70) {
                    new_pixel = (probably(punt / 100.0)) ? cv::Vec4b(0, 0, 0, 255) : cv::Vec4b(92, 36, 60, 255);
                } else if (brightness < 90) {
                    new_pixel = (probably(punt / 100.0)) ? cv::Vec4b(92, 36, 60, 255) : cv::Vec4b(0, 0, 0, 255);
                } else if (brightness < 150) {
                    new_pixel = cv::Vec4b(92, 36, 60, 255);
                } else if (brightness < 200) {
                    new_pixel = (probably(punt / 100.0)) ? cv::Vec4b(203, 43, 43, 255) : cv::Vec4b(92, 36, 60, 255);
                } else {
                    new_pixel = cv::Vec4b(203, 43, 43, 255);
                }
            }

            imag.at<cv::Vec3b>(y, x) = cv::Vec3b(new_pixel[0], new_pixel[1], new_pixel[2]);
        }
    }

    cv::cvtColor(imag, imag, cv::COLOR_RGB2BGR);

    return imag;
}

void processFrameRange(const std::vector<std::string>& frameFiles, int startIdx, int endIdx, const std::string& inputFolder, const std::string& outputFolder, int milkType, int quality, bool effect) {
    for (int i = startIdx; i <= endIdx; ++i) {
        std::string framePath = inputFolder + "/" + frameFiles[i];
        cv::Mat frame = cv::imread(framePath);
        if (!frame.empty()) {
            cv::Mat filteredFrame = applyFilter(frame, true, effect, milkType, quality, framePath);
            std::string outputFramePath = outputFolder + "/" + frameFiles[i];
            cv::imwrite(outputFramePath, filteredFrame);
        }
    }
}

void processFramesWithThreads(const std::string& inputFolder, const std::string& outputFolder, int milkType, int quality, bool effect, int numThreads) {
    fs::create_directory(outputFolder);

    std::vector<std::string> frameFiles;
    for (const auto& entry : fs::directory_iterator(inputFolder)) {
        frameFiles.push_back(entry.path().filename().string());
    }

    std::sort(frameFiles.begin(), frameFiles.end());

    int totalFrames = frameFiles.size();
    int framesPerThread = totalFrames / numThreads;
    std::vector<std::thread> threads;

    for (int i = 0; i < numThreads; ++i) {
        int startIdx = i * framesPerThread;
        int endIdx = (i == numThreads - 1) ? totalFrames - 1 : (i + 1) * framesPerThread - 1;
        threads.emplace_back(processFrameRange, frameFiles, startIdx, endIdx, inputFolder, outputFolder, milkType, quality, effect);
    }

    for (auto& t : threads) {
        t.join();
    }
}

void framesToVideo(const std::string& inputFolder, const std::string& outputPath, int fps, const std::string& originalVideoPath) {
    std::string command = "ffmpeg -y -framerate " + std::to_string(fps) + " -i " + inputFolder + "/frame%06d.jpg -i " + originalVideoPath + " -c:v libx264 -c:a aac -strict experimental -pix_fmt yuv420p -shortest " + outputPath;
    std::system(command.c_str());
}

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "Usage: " << argv[0] << " <video_path>" << std::endl;
        return 1;
    }

    std::string videoPath = argv[1];
    std::string videoName = fs::path(videoPath).stem().string();
    std::string videoExt = fs::path(videoPath).extension().string();
    std::string filteredVideoPath = videoName + "_filtered" + videoExt;

    int originalFPS = getVideoFPS(videoPath);
    int fps = originalFPS;

    char customizeFPS;
    std::cout << "Would you like to customize the FPS for frame extraction? (y/n): ";
    std::cin >> customizeFPS;
    if (customizeFPS == 'y' || customizeFPS == 'Y') {
        std::cout << "Enter the desired FPS for frame extraction: ";
        std::cin >> fps;
    } else {
        fps = originalFPS;
    }

    extractFrames(videoPath, "og", fps);

    int milkType = 1;
    bool pointillism = false;
    bool compression = false;
    int quality = 90;
    int numThreads = std::thread::hardware_concurrency();

    std::cout << "Select milk type (1 or 2): ";
    std::cin >> milkType;
    std::cout << "Apply pointillism effect? (0 for no, 1 for yes): ";
    std::cin >> pointillism;
    std::cout << "Apply compression? (0 for no, 1 for yes): ";
    std::cin >> compression;
    if (compression) {
        std::cout << "Enter compression quality (0-100, where 0 is best quality): ";
        std::cin >> quality;
    }

    std::cout << "Using " << numThreads << " threads for processing." << std::endl;

    processFramesWithThreads("og", "filtered_frames", milkType, quality, pointillism, numThreads);

    framesToVideo("filtered_frames", filteredVideoPath, fps, videoPath);

    fs::remove_all("filtered_frames");
    fs::remove_all("og");

    return 0;
}